"""Unit tests for CLI parser and error conditions."""

import os
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.cli import build_parser, main
from git_stats_lite.git import GitError


class TestCLI(unittest.TestCase):
    def test_invalid_dates_fail_before_git(self) -> None:
        for option in ("--since", "--until"):
            for value in ("garbage", "2026-02-30", "2025-02-29", "2026-13-01", "2026-01-01T25:00:00", "-3d", "1.5m", "", "20260101"):
                with (
                    self.subTest(option=option, value=value),
                    patch("git_stats_lite.cli.is_git_available", side_effect=AssertionError("Git must not run")),
                    patch("sys.stderr", new_callable=StringIO) as stderr,
                ):
                    with self.assertRaises(SystemExit) as cm:
                        main([".", f"{option}={value}"])
                    self.assertEqual(cm.exception.code, 2)
                    self.assertEqual(stderr.getvalue().splitlines()[-1], f"git-stats: error: invalid {option} value '{value}'")

    def test_valid_dates_reach_git(self) -> None:
        for option in ("--since", "--until"):
            for value in ("1y", "6m", "2w", "30d", "12h", "0d", "2024-02-29", "2026-01-01T12:30:00Z", "2026-01-01T12:30:00+03:00"):
                with (
                    self.subTest(option=option, value=value),
                    patch("git_stats_lite.cli.is_git_available", return_value=False) as git_available,
                    patch("sys.stderr", new_callable=StringIO),
                ):
                    self.assertEqual(main([".", option, value]), 1)
                    git_available.assert_called_once_with()

    def test_invalid_numeric_options_fail_before_git(self) -> None:
        for option, values in (("--bus-factor-months", ("-3", "bad")), ("--top", ("0", "-1", "bad"))):
            for value in values:
                with (
                    self.subTest(option=option, value=value),
                    patch("git_stats_lite.cli.is_git_available", side_effect=AssertionError("Git must not run")),
                    patch("sys.stderr", new_callable=StringIO) as stderr,
                ):
                    with self.assertRaises(SystemExit) as cm:
                        main([".", option, value])
                    self.assertEqual(cm.exception.code, 2)
                    self.assertIn(f"argument {option}:", stderr.getvalue())

    def test_numeric_boundaries(self) -> None:
        args = build_parser().parse_args(["--bus-factor-months", "0", "--top", "1"])
        self.assertEqual(args.bus_factor_months, 0)
        self.assertEqual(args.top, 1)

    def test_unknown_revision_has_friendly_error(self) -> None:
        for option in ("--branch", "--rev"):
            with (
                self.subTest(option=option),
                patch("sys.stderr", new_callable=StringIO) as stderr,
                patch("sys.stdout", new_callable=StringIO) as stdout,
            ):
                self.assertEqual(main([".", option, "no-such-revision-for-cli-test"]), 1)
                self.assertEqual(stderr.getvalue(), "Git error: unknown branch or revision 'no-such-revision-for-cli-test'\n")
                self.assertEqual(stdout.getvalue(), "")

    def test_parser_defaults(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.path, ".")
        self.assertEqual(args.format, "terminal")
        self.assertEqual(args.bus_factor_months, 6)
        self.assertEqual(args.top, 10)
        self.assertEqual(args.tz, "local")
        self.assertFalse(args.anonymize)

    def test_parser_custom_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "/repo",
            "--since", "1y",
            "--until", "2026-06-01",
            "--branch", "feature",
            "--bus-factor-months", "12",
            "--top", "25",
            "--tz", "utc",
            "--anonymize",
            "--html", "report.html",
        ])
        self.assertEqual(args.path, "/repo")
        self.assertEqual(args.since, "1y")
        self.assertEqual(args.until, "2026-06-01")
        self.assertEqual(args.revision, "feature")
        self.assertEqual(args.bus_factor_months, 12)
        self.assertEqual(args.top, 25)
        self.assertEqual(args.tz, "utc")
        self.assertTrue(args.anonymize)
        self.assertEqual(args.html, "report.html")

    def test_version_flag(self) -> None:
        with self.assertRaises(SystemExit) as cm:
            main(["--version"])
        self.assertEqual(cm.exception.code, 0)

    def test_nonexistent_path(self) -> None:
        exit_code = main(["/path/that/does/not/exist/anywhere"])
        self.assertEqual(exit_code, 1)

    def test_non_git_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main([tmpdir])
            self.assertEqual(exit_code, 1)

    def test_git_unavailable(self) -> None:
        with patch("git_stats_lite.cli.is_git_available", return_value=False):
            self.assertEqual(main(["."]), 1)

    def test_git_repo_root_error(self) -> None:
        with patch("git_stats_lite.cli.get_repo_root", side_effect=GitError("root error")):
            self.assertEqual(main(["."]), 1)

    def test_git_analysis_git_error(self) -> None:
        with patch("git_stats_lite.cli.stream_git_log", side_effect=GitError("log error")):
            self.assertEqual(main(["."]), 1)

    def test_git_analysis_unexpected_error(self) -> None:
        with patch("git_stats_lite.cli.stream_git_log", side_effect=RuntimeError("unexpected")):
            self.assertEqual(main(["."]), 1)

    def test_mailmap_missing_warning(self) -> None:
        # Should warn to stderr but proceed
        exit_code = main([".", "--mailmap", "/nonexistent/mailmap.txt", "--top", "1"])
        self.assertEqual(exit_code, 0)

    def test_mailmap_existing_file(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("Canonical <can@example.com> <old@example.com>\n")
            f_path = f.name
        try:
            exit_code = main([".", "--mailmap", f_path, "--top", "1"])
            self.assertEqual(exit_code, 0)
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)

    def test_exports_and_formats(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = os.path.join(tmpdir, "out.html")
            json_file = os.path.join(tmpdir, "out.json")
            md_file = os.path.join(tmpdir, "out.md")
            out_file = os.path.join(tmpdir, "terminal.txt")

            exit_code = main([
                ".",
                "--html", html_file,
                "--json", json_file,
                "--markdown", md_file,
                "-o", out_file,
                "--anonymize",
                "--top", "3",
            ])
            self.assertEqual(exit_code, 0)
            self.assertTrue(os.path.isfile(html_file))
            self.assertTrue(os.path.isfile(json_file))
            self.assertTrue(os.path.isfile(md_file))
            self.assertTrue(os.path.isfile(out_file))

    def test_direct_format_flags(self) -> None:
        # Test --json stdout flag
        self.assertEqual(main([".", "--json", "--top", "2"]), 0)
        # Test --markdown stdout flag
        self.assertEqual(main([".", "--markdown", "--top", "2"]), 0)
        # Test --html stdout flag
        self.assertEqual(main([".", "--html", "--top", "2"]), 0)
        # Test format flag directly
        self.assertEqual(main([".", "--format", "json", "--top", "2"]), 0)
        self.assertEqual(main([".", "--format", "markdown", "--top", "2"]), 0)
        self.assertEqual(main([".", "--format", "html", "--top", "2"]), 0)

    def test_file_write_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use an invalid path (directory where file expected) to trigger OSError
            bad_path = os.path.join(tmpdir, "nonexistent_sub", "file.out")
            self.assertEqual(main([".", "--html", bad_path]), 1)
            self.assertEqual(main([".", "--json", bad_path]), 1)
            self.assertEqual(main([".", "--markdown", bad_path]), 1)
            self.assertEqual(main([".", "-o", bad_path]), 1)

    def test_main_module_execution(self) -> None:
        import runpy
        with patch.object(sys, "argv", ["git-stats", "--help"]):
            with self.assertRaises(SystemExit) as cm:
                runpy.run_module("git_stats_lite", run_name="__main__")
            self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
