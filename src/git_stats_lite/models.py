"""Data models for git-stats-lite."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FileDiff:
    """Represents a single file modification within a commit."""

    path: str
    additions: int = 0
    deletions: int = 0
    is_binary: bool = False
    old_path: str | None = None

    @property
    def total_changes(self) -> int:
        return self.additions + self.deletions


@dataclass
class CommitInfo:
    """Parsed commit record."""

    hash: str
    author_name: str
    author_email: str
    author_date_iso: str
    author_timestamp: int
    committer_date_iso: str
    committer_timestamp: int
    subject: str
    files: list[FileDiff] = field(default_factory=list)


@dataclass
class AuthorStats:
    """Aggregated statistics for a single author."""

    name: str
    email: str
    canonical_email: str
    commits_count: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    lines_changed: int = 0
    first_commit_date: str = ""
    last_commit_date: str = ""
    active_days: int = 0
    percentage_commits: float = 0.0
    percentage_lines: float = 0.0


@dataclass
class FileStats:
    """Aggregated churn and hotspot statistics for a file."""

    path: str
    commits_count: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    lines_changed: int = 0
    hotspot_score: float = 0.0


@dataclass
class LanguageStats:
    """Aggregated statistics for a programming language or file type."""

    language: str
    files_count: int = 0
    commits_count: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    lines_changed: int = 0
    percentage_lines: float = 0.0


@dataclass
class ActivityHeatmap:
    """Weekday (0=Mon .. 6=Sun) x Hour (0 .. 23) matrix."""

    grid: list[list[int]] = field(default_factory=lambda: [[0] * 24 for _ in range(7)])
    timezone_mode: str = "local"
    max_val: int = 0
    total_commits: int = 0


@dataclass
class BusFactorAuthor:
    """Author contribution summary for bus factor calculation."""

    name: str
    email: str
    lines_changed: int
    percentage: float


@dataclass
class BusFactorResult:
    """Bus factor calculation summary."""

    window_months: int
    total_authors_in_window: int
    total_lines_in_window: int
    bus_factor_50: int
    bus_factor_80: int
    authors_50: list[BusFactorAuthor] = field(default_factory=list)
    authors_80: list[BusFactorAuthor] = field(default_factory=list)


@dataclass
class RepoReport:
    """Complete aggregated statistics report for a git repository."""

    repo_name: str
    repo_path: str
    branch: str
    first_commit_date: str | None
    last_commit_date: str | None
    total_commits: int
    total_authors: int
    total_files_touched: int
    total_lines_added: int
    total_lines_deleted: int
    total_lines_changed: int
    active_days_count: int
    authors: list[AuthorStats]
    files: list[FileStats]
    languages: list[LanguageStats]
    heatmap_local: ActivityHeatmap
    heatmap_utc: ActivityHeatmap
    commits_by_day: dict[str, int]
    commits_by_week: dict[str, int]
    bus_factor: BusFactorResult
    is_anonymized: bool
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        """Convert report to JSON-serializable dictionary."""
        return asdict(self)
