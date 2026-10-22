"""Unit tests for git utilities."""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.git import (
    get_current_branch,
    get_repo_root,
    is_git_available,
    is_git_repository,
)


class TestGit(unittest.TestCase):
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
