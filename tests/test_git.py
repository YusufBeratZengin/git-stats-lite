"""Unit tests for git utilities."""

import os
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.git import (
    get_current_branch,
    get_repo_root,
    is_git_available,
    is_git_repository,
    stream_git_log,
)


class TestGit(unittest.TestCase):
    def test_relative_intervals_and_streaming(self):
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

    def test_is_git_available(self):
        self.assertTrue(is_git_available())

    def test_is_git_repository(self):
        curr_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertTrue(is_git_repository(curr_dir))

    def test_get_repo_root(self):
        curr_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root = get_repo_root(curr_dir)
        self.assertTrue(os.path.samefile(root, curr_dir))

    def test_get_current_branch(self):
        curr_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        branch = get_current_branch(curr_dir)
        self.assertIn(branch, ["main", "HEAD"])


if __name__ == "__main__":
    unittest.main()
