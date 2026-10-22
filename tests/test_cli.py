"""Unit tests for CLI parser and error conditions."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.cli import build_parser, main


class TestCLI(unittest.TestCase):
    def test_parser_defaults(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.path, ".")
        self.assertEqual(args.format, "terminal")
        self.assertEqual(args.bus_factor_months, 6)
        self.assertEqual(args.top, 10)
        self.assertEqual(args.tz, "local")
        self.assertFalse(args.anonymize)

    def test_parser_custom_args(self):
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

    def test_nonexistent_path(self):
        exit_code = main(["/path/that/does/not/exist/anywhere"])
        self.assertEqual(exit_code, 1)

    def test_non_git_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main([tmpdir])
            self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
