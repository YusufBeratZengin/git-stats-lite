"""Unit tests for git log streaming parser and normalization."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.parser import (
    MailmapLookup,
    normalize_email,
    parse_git_log_stream,
    resolve_rename_path,
)


class TestParser(unittest.TestCase):
    def test_normalize_email_github_noreply(self):
        self.assertEqual(
            normalize_email("42+YusufBeratZengin@users.noreply.github.com"),
            "yusufberatzengin@users.noreply.github.com",
        )
        self.assertEqual(
            normalize_email("YusufBeratZengin@users.noreply.github.com"),
            "yusufberatzengin@users.noreply.github.com",
        )
        self.assertEqual(
            normalize_email("99+YusufBeratZengin@users.noreply.github.com"),
            "yusufberatzengin@users.noreply.github.com",
        )

    def test_normalize_email_gitlab_noreply(self):
        self.assertEqual(
            normalize_email("42-contributor@users.noreply.gitlab.com"),
            "contributor@users.noreply.gitlab.com",
        )

    def test_normalize_email_standard(self):
        self.assertEqual(normalize_email("Dev@Company.EXAMPLE"), "dev@company.example")
        self.assertEqual(normalize_email("<dev@example.org>"), "dev@example.org")
        self.assertEqual(normalize_email(""), "")

    def test_resolve_rename_path(self):
        self.assertEqual(resolve_rename_path("src/foo.py"), "src/foo.py")
        self.assertEqual(resolve_rename_path("src/{old => new}/main.py"), "src/new/main.py")
        self.assertEqual(resolve_rename_path("old_dir/test.py => new_dir/test.py"), "new_dir/test.py")
        self.assertEqual(resolve_rename_path("{old => new}/README.md"), "new/README.md")
        self.assertEqual(resolve_rename_path("dir/{old => }/file.txt"), "dir/file.txt")

    def test_mailmap_lookup(self):
        mailmap = MailmapLookup()
        # Proper Name <proper@email.xx> Commit Name <commit@email.xx>
        mailmap.add_line("Canonical contributor A <jane@canonical.example> Alias A <jdoe@legacy.example>")
        # Proper Name <proper@email.xx> <commit@email.xx>
        mailmap.add_line("Canonical contributor B <john@canonical.example> <john@alias.example>")
        # Proper Name <commit@email.xx>
        mailmap.add_line("Canonical contributor C <alex@work.example>")

        # Test exact match
        name, email = mailmap.lookup("Alias A", "jdoe@legacy.example")
        self.assertEqual(name, "Canonical contributor A")
        self.assertEqual(email, "jane@canonical.example")

        # Test email-only match
        name, email = mailmap.lookup("Alias B", "john@alias.example")
        self.assertEqual(name, "Canonical contributor B")
        self.assertEqual(email, "john@canonical.example")

        # Test proper name only
        name, email = mailmap.lookup("Alias C", "alex@work.example")
        self.assertEqual(name, "Canonical contributor C")
        self.assertEqual(email, "alex@work.example")

        # Unmatched falls back to input
        name, email = mailmap.lookup("Random", "random@domain.example")
        self.assertEqual(name, "Random")
        self.assertEqual(email, "random@domain.example")

    def test_parse_git_log_stream(self):
        raw_lines = [
            "@@@COMMIT@@@\x00abc123\x00Contributor A\x00alice@example.com\x002026-05-10T14:30:00+02:00\x001778416200\x002026-05-10T14:30:00+02:00\x001778416200\x00Initial commit",
            "10\t2\tsrc/main.py",
            "5\t0\tREADME.md",
            "-\t-\tassets/logo.png",
            "",
            "@@@COMMIT@@@\x00def456\x00Contributor B\x00bob@example.com\x002026-05-11T10:00:00Z\x001778486400\x002026-05-11T10:00:00Z\x001778486400\x00Fix issue",
            "3\t1\tsrc/main.py",
        ]

        commits = list(parse_git_log_stream(raw_lines))
        self.assertEqual(len(commits), 2)

        c1 = commits[0]
        self.assertEqual(c1.hash, "abc123")
        self.assertEqual(c1.author_name, "Contributor A")
        self.assertEqual(c1.subject, "Initial commit")
        self.assertEqual(len(c1.files), 3)
        self.assertEqual(c1.files[0].path, "src/main.py")
        self.assertEqual(c1.files[0].additions, 10)
        self.assertEqual(c1.files[0].deletions, 2)
        self.assertEqual(c1.files[1].path, "README.md")
        self.assertTrue(c1.files[2].is_binary)
        self.assertEqual(c1.files[2].additions, 0)

        c2 = commits[1]
        self.assertEqual(c2.hash, "def456")
        self.assertEqual(c2.author_name, "Contributor B")
        self.assertEqual(len(c2.files), 1)
        self.assertEqual(c2.files[0].additions, 3)
        self.assertEqual(c2.files[0].deletions, 1)


if __name__ == "__main__":
    unittest.main()
