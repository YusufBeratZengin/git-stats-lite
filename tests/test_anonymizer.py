"""Unit tests for author anonymization."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.anonymizer import Anonymizer


class TestAnonymizer(unittest.TestCase):
    def setUp(self):
        self.anon = Anonymizer()

    def test_deterministic_hashing(self):
        name1, email1 = self.anon.anonymize_author("Alice Smith", "alice@example.com")
        name2, email2 = self.anon.anonymize_author("Alice Smith", "alice@example.com")

        self.assertEqual(name1, name2)
        self.assertEqual(email1, email2)
        self.assertTrue(name1.startswith("Author-"))
        self.assertTrue(email1.startswith("anon-"))
        self.assertTrue(email1.endswith("@privacy.local"))

    def test_different_authors_get_different_tokens(self):
        name_a, _ = self.anon.anonymize_author("Alice", "alice@example.com")
        name_b, _ = self.anon.anonymize_author("Bob", "bob@example.com")

        self.assertNotEqual(name_a, name_b)

    def test_fallback_when_email_missing(self):
        name1, email1 = self.anon.anonymize_author("Charlie", "")
        self.assertTrue(name1.startswith("Author-"))
        self.assertTrue(email1.startswith("anon-"))

    def test_helper_methods(self):
        name = self.anon.anonymize_name("Dave", "dave@example.com")
        email = self.anon.anonymize_email("dave@example.com", "Dave")
        self.assertTrue(name.startswith("Author-"))
        self.assertTrue(email.startswith("anon-"))


if __name__ == "__main__":
    unittest.main()
