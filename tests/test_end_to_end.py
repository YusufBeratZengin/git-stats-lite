"""End-to-end integration tests using scripted temporary git repositories."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.cli import main


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_dir = self.temp_dir.name

        # Initialize git repo
        self._git(["init", "-b", "main"])
        self._git(["config", "user.name", "Test Runner"])
        self._git(["config", "user.email", "runner@example.local"])

    def tearDown(self):
        self.temp_dir.cleanup()

    def _git(self, args, env=None):
        cmd = ["git"] + args
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        res = subprocess.run(
            cmd,
            cwd=self.repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=merged_env,
            check=True,
        )
        return res.stdout

    def _commit(self, message, author_name, author_email, date_iso):
        env = {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_AUTHOR_DATE": date_iso,
            "GIT_COMMITTER_NAME": author_name,
            "GIT_COMMITTER_EMAIL": author_email,
            "GIT_COMMITTER_DATE": date_iso,
        }
        self._git(["add", "."], env=env)
        self._git(["commit", "-m", message], env=env)

    def test_full_metrics_and_outputs(self):
        # 1. First commit by Alice (Python file)
        src_dir = os.path.join(self.repo_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        py_file = os.path.join(src_dir, "calc.py")
        with open(py_file, "w", encoding="utf-8") as f:
            f.write("\n".join([f"def func_{i}(): pass" for i in range(20)]) + "\n")

        self._commit("Add initial calc module", "Alice Smith", "alice@example.com", "2026-01-10T10:00:00+00:00")

        # 2. Second commit by Bob (Modify calc.py and add guide.md)
        docs_dir = os.path.join(self.repo_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        doc_file = os.path.join(docs_dir, "guide.md")
        with open(doc_file, "w", encoding="utf-8") as f:
            f.write("# Guide\n\nIntro documentation.\n")

        with open(py_file, "a", encoding="utf-8") as f:
            f.write("def helper(): return 42\n")

        self._commit("Add guide and helper", "Bob Jones", "bob@example.com", "2026-02-15T14:00:00+00:00")

        # 3. Third commit by Alice using GitHub noreply email
        with open(py_file, "a", encoding="utf-8") as f:
            f.write("def extra(): pass\n")

        self._commit("Add extra logic", "Alice Smith", "12345+AliceSmith@users.noreply.github.com", "2026-03-20T16:00:00+00:00")

        # 4. Fourth commit by Charlie (deploy.sh)
        sh_file = os.path.join(self.repo_dir, "deploy.sh")
        with open(sh_file, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\necho 'Deploying'\n")

        self._commit("Add deploy script", "Charlie Brown", "charlie@example.com", "2026-04-10T18:00:00+00:00")

        # Test CLI Terminal output
        exit_code = main([self.repo_dir])
        self.assertEqual(exit_code, 0)

        # Test CLI JSON export
        json_path = os.path.join(self.repo_dir, "stats.json")
        exit_code = main([self.repo_dir, "--json", json_path])
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.isfile(json_path))

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["total_commits"], 4)
        self.assertGreaterEqual(data["total_lines_added"], 24)
        self.assertEqual(data["total_files_touched"], 3)

        # Check languages detected
        langs = {l["language"]: l for l in data["languages"]}
        self.assertIn("Python", langs)
        self.assertIn("Markdown", langs)
        self.assertIn("Shell", langs)

        # Check Bus Factor calculation
        self.assertIn("bus_factor_50", data["bus_factor"])
        self.assertIn("bus_factor_80", data["bus_factor"])
        self.assertGreaterEqual(data["bus_factor"]["bus_factor_50"], 1)

        # Test HTML report export
        html_path = os.path.join(self.repo_dir, "report.html")
        exit_code = main([self.repo_dir, "--html", html_path])
        self.assertEqual(exit_code, 0)
        self.assertTrue(os.path.isfile(html_path))

        with open(html_path, "r", encoding="utf-8") as f:
            html_text = f.read()

        self.assertIn("<!DOCTYPE html>", html_text)
        self.assertIn("heatmap-svg", html_text)
        self.assertIn("calc.py", html_text)

        # Test Anonymize flag
        anon_json_path = os.path.join(self.repo_dir, "anon_stats.json")
        exit_code = main([self.repo_dir, "--anonymize", "--json", anon_json_path])
        self.assertEqual(exit_code, 0)

        with open(anon_json_path, "r", encoding="utf-8") as f:
            anon_text = f.read()

        self.assertNotIn("Alice Smith", anon_text)
        self.assertNotIn("alice@example.com", anon_text)
        self.assertNotIn("Bob Jones", anon_text)
        self.assertNotIn("bob@example.com", anon_text)
        self.assertNotIn("Charlie Brown", anon_text)
        self.assertNotIn("charlie@example.com", anon_text)
        self.assertIn("Author-", anon_text)
        self.assertIn("@privacy.local", anon_text)

        # Test --since filter (only commits from March onwards)
        since_json_path = os.path.join(self.repo_dir, "since_stats.json")
        exit_code = main([self.repo_dir, "--since", "2026-03-01", "--json", since_json_path])
        self.assertEqual(exit_code, 0)

        with open(since_json_path, "r", encoding="utf-8") as f:
            since_data = json.load(f)

        self.assertEqual(since_data["total_commits"], 2)

    def test_empty_repository(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            subprocess.run(["git", "init", "-b", "main"], cwd=empty_dir, check=True, stdout=subprocess.PIPE)
            # Running CLI on empty repo should exit 0 and not crash
            exit_code = main([empty_dir])
            self.assertEqual(exit_code, 0)

            # JSON export on empty repo
            empty_json = os.path.join(empty_dir, "empty.json")
            exit_code = main([empty_dir, "--format", "json", "-o", empty_json])
            self.assertEqual(exit_code, 0)
            with open(empty_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["total_commits"], 0)

    def test_mailmap_in_repo(self):
        # Create a repo with a .mailmap file
        with tempfile.TemporaryDirectory() as mm_dir:
            def _run(args, env=None):
                merged = os.environ.copy()
                if env:
                    merged.update(env)
                subprocess.run(["git"] + args, cwd=mm_dir, check=True, stdout=subprocess.PIPE, env=merged)

            _run(["init", "-b", "main"])
            _run(["config", "user.name", "Initial"])
            _run(["config", "user.email", "init@example.com"])

            # Add .mailmap
            mm_file = os.path.join(mm_dir, ".mailmap")
            with open(mm_file, "w", encoding="utf-8") as f:
                f.write("Jane Doe <jane@canonical.org> J. Doe <jdoe@legacy.org>\n")

            dummy_file = os.path.join(mm_dir, "test.py")
            with open(dummy_file, "w", encoding="utf-8") as f:
                f.write("print('hello')\n")

            _run(["add", "."])
            env = {
                "GIT_AUTHOR_NAME": "J. Doe",
                "GIT_AUTHOR_EMAIL": "jdoe@legacy.org",
                "GIT_COMMITTER_NAME": "J. Doe",
                "GIT_COMMITTER_EMAIL": "jdoe@legacy.org",
            }
            _run(["commit", "-m", "Commit by legacy alias"], env=env)

            out_json = os.path.join(mm_dir, "out.json")
            exit_code = main([mm_dir, "--json", out_json])
            self.assertEqual(exit_code, 0)

            with open(out_json, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(data["total_commits"], 1)
            # Mailmap should resolve J. Doe -> Jane Doe
            self.assertEqual(data["authors"][0]["name"], "Jane Doe")
            self.assertEqual(data["authors"][0]["email"], "jane@canonical.org")


if __name__ == "__main__":
    unittest.main()
