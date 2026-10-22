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
            normalize_email("118852217+YusufBeratZengin@users.noreply.github.com"),
            "yusufberatzengin@users.noreply.github.com",
        )
        self.assertEqual(
            normalize_email("alice@users.noreply.github.com"),
            "alice@users.noreply.github.com",
        )
        self.assertEqual(
            normalize_email("99999+john-doe@users.noreply.github.com"),
            "john-doe@users.noreply.github.com",
        )

    def test_normalize_email_gitlab_noreply(self):
        self.assertEqual(
            normalize_email("1234-bob@users.noreply.gitlab.com"),
            "bob@users.noreply.gitlab.com",
        )

    def test_normalize_email_standard(self):
        self.assertEqual(normalize_email("Dev@Company.COM"), "dev@company.com")
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
        mailmap.add_line("Jane Doe <jane@canonical.org> J. Doe <jdoe@legacy.org>")
        # Proper Name <proper@email.xx> <commit@email.xx>
        mailmap.add_line("John Smith <john@canonical.org> <john@alias.net>")
        # Proper Name <commit@email.xx>
        mailmap.add_line("Alex Rivers <alex@work.com>")

        # Test exact match
        name, email = mailmap.lookup("J. Doe", "jdoe@legacy.org")
        self.assertEqual(name, "Jane Doe")
        self.assertEqual(email, "jane@canonical.org")

        # Test email-only match
        name, email = mailmap.lookup("Johnny", "john@alias.net")
        self.assertEqual(name, "John Smith")
        self.assertEqual(email, "john@canonical.org")

        # Test proper name only
        name, email = mailmap.lookup("Alex", "alex@work.com")
        self.assertEqual(name, "Alex Rivers")
        self.assertEqual(email, "alex@work.com")

        # Unmatched falls back to input
        name, email = mailmap.lookup("Random", "random@domain.com")
        self.assertEqual(name, "Random")
        self.assertEqual(email, "random@domain.com")

    def test_parse_git_log_stream(self):
        raw_lines = [
            "@@@COMMIT@@@\x00abc123\x00Alice\x00alice@example.com\x002026-05-10T14:30:00+02:00\x001778416200\x002026-05-10T14:30:00+02:00\x001778416200\x00Initial commit",
            "10\t2\tsrc/main.py",
            "5\t0\tREADME.md",
            "-\t-\tassets/logo.png",
            "",
            "@@@COMMIT@@@\x00def456\x00Bob\x00bob@example.com\x002026-05-11T10:00:00Z\x001778486400\x002026-05-11T10:00:00Z\x001778486400\x00Fix issue",
            "3\t1\tsrc/main.py",
        ]

        commits = list(parse_git_log_stream(raw_lines))
        self.assertEqual(len(commits), 2)

        c1 = commits[0]
        self.assertEqual(c1.hash, "abc123")
        self.assertEqual(c1.author_name, "Alice")
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
        self.assertEqual(c2.author_name, "Bob")
        self.assertEqual(len(c2.files), 1)
        self.assertEqual(c2.files[0].additions, 3)
        self.assertEqual(c2.files[0].deletions, 1)


if __name__ == "__main__":
    unittest.main()
