"""Unit tests for git utilities."""

import os
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.git import (
    GitError,
    get_current_branch,
    get_repo_root,
    is_git_available,
    is_git_repository,
    stream_git_log,
)


class TestGit(unittest.TestCase):
    def test_relative_intervals_and_streaming(self) -> None:
        for since, until in [("1y", "6m"), ("2026-01-01", "2026-06-01")]:
            with self.subTest(since=since), patch("git_stats_lite.git.subprocess.Popen") as popen:
                process = MagicMock()
                process.stdout = StringIO("first\nsecond\n")
                process.stderr = StringIO("")
                process.returncode = 0
                popen.return_value = process
                self.assertEqual(list(stream_git_log(".", since=since, until=until)), ["first\n", "second\n"])
                command = popen.call_args.args[0]
                expected_since = "1 years ago" if since == "1y" else since
                expected_until = "6 months ago" if until == "6m" else until
                self.assertIn(f"--since={expected_since}", command)
                self.assertIn(f"--until={expected_until}", command)
                process.wait.assert_called_once()

    def test_stream_git_log_flags(self) -> None:
        with patch("git_stats_lite.git.subprocess.Popen") as popen:
            process = MagicMock()
            process.stdout = StringIO("")
            process.stderr = StringIO("")
            process.returncode = 0
            popen.return_value = process
            list(stream_git_log(".", revision="v1.0", all_branches=True))
            command = popen.call_args.args[0]
            self.assertIn("--all", command)
            self.assertIn("v1.0", command)

    def test_stream_git_log_empty_repo(self) -> None:
        with patch("git_stats_lite.git.subprocess.Popen") as popen:
            process = MagicMock()
            process.stdout = StringIO("")
            process.stderr = StringIO("fatal: your current branch 'main' does not have any commits yet")
            process.returncode = 128
            popen.return_value = process
            lines = list(stream_git_log("."))
            self.assertEqual(lines, [])

    def test_stream_git_log_error(self) -> None:
        with patch("git_stats_lite.git.subprocess.Popen") as popen:
            process = MagicMock()
            process.stdout = StringIO("")
            process.stderr = StringIO("fatal: ambiguous argument 'unknown': unknown revision")
            process.returncode = 128
            popen.return_value = process
            with self.assertRaisesRegex(GitError, "^unknown branch or revision 'unknown'$"):
                list(stream_git_log(".", revision="unknown"))

    def test_other_git_errors_are_not_misreported_as_unknown_revision(self) -> None:
        with patch("git_stats_lite.git.subprocess.Popen") as popen:
            process = MagicMock()
            process.stdout = StringIO("")
            process.stderr = StringIO("fatal: unable to read tree")
            process.returncode = 128
            popen.return_value = process
            with self.assertRaisesRegex(GitError, "unable to read tree"):
                list(stream_git_log(".", revision="HEAD"))

    def test_is_git_available(self) -> None:
        self.assertTrue(is_git_available())

    def test_is_git_available_file_not_found(self) -> None:
        with patch("git_stats_lite.git.subprocess.run", side_effect=FileNotFoundError):
            self.assertFalse(is_git_available())

    def test_is_git_repository(self) -> None:
        curr_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(is_git_repository(curr_dir))

    def test_is_git_repository_false_and_error(self) -> None:
        with patch("git_stats_lite.git.subprocess.run", side_effect=FileNotFoundError):
            self.assertFalse(is_git_repository("/fake/path"))

    def test_get_repo_root(self) -> None:
        curr_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root = get_repo_root(curr_dir)
        self.assertTrue(os.path.samefile(root, curr_dir))

    def test_get_repo_root_error(self) -> None:
        import subprocess
        with (
            patch("git_stats_lite.git.subprocess.run", side_effect=subprocess.CalledProcessError(128, "git", stderr="not a repo")),
            self.assertRaises(GitError),
        ):
            get_repo_root("/fake/path")

    def test_get_current_branch(self) -> None:
        curr_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        branch = get_current_branch(curr_dir)
        self.assertIn(branch, ["main", "HEAD"])

    def test_get_current_branch_detached(self) -> None:
        # First call returns empty branch, second call returns short hash
        res1 = MagicMock(stdout="", returncode=0)
        res2 = MagicMock(stdout="a1b2c3d\n", returncode=0)
        with patch("git_stats_lite.git.subprocess.run", side_effect=[res1, res2]):
            self.assertEqual(get_current_branch("."), "a1b2c3d")

    def test_get_current_branch_oserror(self) -> None:
        with patch("git_stats_lite.git.subprocess.run", side_effect=OSError):
            self.assertEqual(get_current_branch("."), "HEAD")


if __name__ == "__main__":
    unittest.main()


class TestNonAsciiPaths(unittest.TestCase):
    def test_repo_root_and_branch_survive_non_ascii_directory(self) -> None:
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory(prefix="gsl-") as base:
            repo = Path(base) / "proje ğüşiöç"
            repo.mkdir()
            env = {**os.environ, "GIT_AUTHOR_NAME": "A", "GIT_AUTHOR_EMAIL": "a@x.test",
                   "GIT_COMMITTER_NAME": "A", "GIT_COMMITTER_EMAIL": "a@x.test"}
            subprocess.run(["git", "init", "-q", "-b", "ana"], cwd=repo, check=True)
            (repo / "a.txt").write_text("x", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-qm", "x"], cwd=repo, check=True, env=env,
                           capture_output=True)
            root = get_repo_root(str(repo))
            self.assertTrue(os.path.samefile(root, repo))
            self.assertEqual(get_current_branch(root), "ana")


class TestQuotePath(unittest.TestCase):
    def test_non_ascii_file_names_are_not_octal_quoted(self) -> None:
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory(prefix="gsl-") as base:
            repo = Path(base)
            env = {**os.environ, "GIT_AUTHOR_NAME": "A", "GIT_AUTHOR_EMAIL": "a@x.test",
                   "GIT_COMMITTER_NAME": "A", "GIT_COMMITTER_EMAIL": "a@x.test"}
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            (repo / "çalışma notu.txt").write_text("x", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-qm", "x"], cwd=repo, check=True, env=env,
                           capture_output=True)
            output = "".join(stream_git_log(str(repo)))
            self.assertIn("çalışma notu.txt", output)
            self.assertNotIn('"', output.split("\n", 2)[-1])
