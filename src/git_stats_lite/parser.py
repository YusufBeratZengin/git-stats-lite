"""Streaming parser for git log output and mailmap normalization."""

from __future__ import annotations

import os
import re
from collections.abc import Generator, Iterable

from .models import CommitInfo, FileDiff

RE_GITHUB_NOREPLY = re.compile(r"^(?:\d+\+)?([a-zA-Z0-9_-]+)@users\.noreply\.github\.com$", re.IGNORECASE)
RE_GITLAB_NOREPLY = re.compile(r"^(?:\d+-)?([a-zA-Z0-9_-]+)@users\.noreply\.gitlab\.com$", re.IGNORECASE)


def normalize_email(email: str) -> str:
    """Normalize email address, lowercasing and resolving common noreply aliases."""
    if not email:
        return ""

    cleaned = email.strip().strip("<>\"'").lower()

    gh_match = RE_GITHUB_NOREPLY.match(cleaned)
    if gh_match:
        return f"{gh_match.group(1)}@users.noreply.github.com"

    gl_match = RE_GITLAB_NOREPLY.match(cleaned)
    if gl_match:
        return f"{gl_match.group(1)}@users.noreply.gitlab.com"

    return cleaned


def resolve_rename_path(path: str) -> str:
    """Resolve git rename notation to the target destination file path.

    Handles:
      - 'a/b.py => a/c.py' -> 'a/c.py'
      - 'dir/{old => new}/file.py' -> 'dir/new/file.py'
      - '{old => new}/file.py' -> 'new/file.py'
      - 'dir/{old => }/file.py' -> 'dir/file.py'
    """
    if "=>" not in path:
        return path

    def _replace_braces(match: re.Match[str]) -> str:
        parts = match.group(1).split("=>")
        if len(parts) >= 2:
            return parts[1].strip()
        return match.group(0)

    # Replace brace groups first
    res = re.sub(r"\{([^}]+)\}", _replace_braces, path)
    if "=>" in res:
        parts = res.split("=>")
        res = parts[-1].strip()

    # Clean double slashes
    while "//" in res:
        res = res.replace("//", "/")
    return res


class MailmapLookup:
    """In-memory parser and resolver for .mailmap files."""

    def __init__(self) -> None:
        # Key: (commit_name_lower, commit_email_lower) or ("", commit_email_lower)
        self._exact_map: dict[tuple[str, str], tuple[str, str]] = {}
        self._email_map: dict[str, tuple[str, str]] = {}
        self._name_map: dict[str, tuple[str, str]] = {}

    @classmethod
    def from_file(cls, path: str) -> MailmapLookup:
        lookup = cls()
        if not os.path.isfile(path):
            return lookup
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    lookup.add_line(line)
        except OSError:
            pass
        return lookup

    def add_line(self, line: str) -> None:
        """Parse a single .mailmap specification line according to git-mailmap format."""
        line = line.strip()
        if not line or line.startswith("#"):
            return

        # Pattern: Proper Name <proper@email.xx> Commit Name <commit@email.xx>
        # Or: Proper Name <proper@email.xx> <commit@email.xx>
        # Or: <proper@email.xx> <commit@email.xx>
        # Or: Proper Name <commit@email.xx>
        pattern = re.compile(r"^(?:([^<]+?)\s+)?<([^>]+)>(?:\s+([^<]+?))?(?:\s+<([^>]+)>)?$")
        match = pattern.match(line)
        if not match:
            return

        proper_name = (match.group(1) or "").strip()
        proper_email = (match.group(2) or "").strip()
        commit_name = (match.group(3) or "").strip()
        commit_email = (match.group(4) or "").strip()

        if commit_email:
            # Proper Name <proper@email> Commit Name <commit@email>
            # or Proper Name <proper@email> <commit@email>
            c_email_low = commit_email.lower()
            if commit_name:
                self._exact_map[(commit_name.lower(), c_email_low)] = (proper_name, proper_email)
            else:
                self._email_map[c_email_low] = (proper_name, proper_email)
        elif proper_name and proper_email:
            # Proper Name <commit@email>
            self._name_map[proper_email.lower()] = (proper_name, proper_email)

    def lookup(self, name: str, email: str) -> tuple[str, str]:
        """Resolve an author name and email to their canonical identity."""
        n_low = name.strip().lower()
        e_low = email.strip().lower()

        # 1. Exact match (name + email)
        if (n_low, e_low) in self._exact_map:
            p_name, p_email = self._exact_map[(n_low, e_low)]
            return (p_name or name, p_email or email)

        # 2. Match commit email -> proper name & proper email
        if e_low in self._email_map:
            p_name, p_email = self._email_map[e_low]
            return (p_name or name, p_email or email)

        # 3. Match commit email -> proper name only
        if e_low in self._name_map:
            p_name, p_email = self._name_map[e_low]
            return (p_name or name, p_email or email)

        return (name, email)


def parse_git_log_stream(lines: Iterable[str], mailmap: MailmapLookup | None = None) -> Generator[CommitInfo, None, None]:
    """Parse git log stream lines into CommitInfo records on the fly."""
    current_commit: CommitInfo | None = None

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if not line:
            continue

        if line.startswith("@@@COMMIT@@@\x00"):
            if current_commit is not None:
                yield current_commit

            parts = line.split("\x00")
            # Format: @@@COMMIT@@@, hash, author_name, author_email, author_date_iso, author_ts, committer_iso, committer_ts, subject
            commit_hash = parts[1] if len(parts) > 1 else ""
            author_name = parts[2] if len(parts) > 2 else ""
            author_email = parts[3] if len(parts) > 3 else ""
            author_date_iso = parts[4] if len(parts) > 4 else ""
            author_ts = int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else 0
            committer_date_iso = parts[6] if len(parts) > 6 else ""
            committer_ts = int(parts[7]) if len(parts) > 7 and parts[7].isdigit() else 0
            subject = parts[8] if len(parts) > 8 else ""

            if mailmap:
                author_name, author_email = mailmap.lookup(author_name, author_email)

            current_commit = CommitInfo(
                hash=commit_hash,
                author_name=author_name,
                author_email=author_email,
                author_date_iso=author_date_iso,
                author_timestamp=author_ts,
                committer_date_iso=committer_date_iso,
                committer_timestamp=committer_ts,
                subject=subject,
                files=[],
            )
        elif current_commit is not None:
            # Numstat line: additions \t deletions \t path
            tokens = line.split("\t", 2)
            if len(tokens) == 3:
                add_str, del_str, raw_path = tokens
                is_binary = add_str == "-" or del_str == "-"
                additions = 0 if is_binary else (int(add_str) if add_str.isdigit() else 0)
                deletions = 0 if is_binary else (int(del_str) if del_str.isdigit() else 0)
                resolved_path = resolve_rename_path(raw_path)

                current_commit.files.append(
                    FileDiff(
                        path=resolved_path,
                        additions=additions,
                        deletions=deletions,
                        is_binary=is_binary,
                    )
                )

    if current_commit is not None:
        yield current_commit
