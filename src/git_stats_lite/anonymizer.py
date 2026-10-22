"""Privacy-preserving anonymization for author identities."""

from __future__ import annotations

import hashlib


class Anonymizer:
    """Deterministically anonymizes author names and email addresses using SHA-256."""

    def __init__(self, salt: str = "git-stats-lite-salt") -> None:
        self.salt = salt
        self._name_map: dict[str, str] = {}
        self._email_map: dict[str, str] = {}

    def _hash_token(self, value: str) -> str:
        """Create a short 8-hex-character hash from a string value."""
        norm = value.strip().lower()
        hasher = hashlib.sha256()
        hasher.update(self.salt.encode("utf-8"))
        hasher.update(b":")
        hasher.update(norm.encode("utf-8"))
        return hasher.hexdigest()[:8]

    def anonymize_author(self, name: str, email: str) -> tuple[str, str]:
        """Return (anonymized_name, anonymized_email).

        The identity is keyed by the normalized email if present, or by name.
        """
        key = (email.strip().lower() if email.strip() else name.strip().lower())
        token = self._hash_token(key)

        if key not in self._name_map:
            self._name_map[key] = f"Author-{token}"
            self._email_map[key] = f"anon-{token}@privacy.local"

        return self._name_map[key], self._email_map[key]

    def anonymize_name(self, name: str, email: str = "") -> str:
        return self.anonymize_author(name, email)[0]

    def anonymize_email(self, email: str, name: str = "") -> str:
        return self.anonymize_author(name, email)[1]
