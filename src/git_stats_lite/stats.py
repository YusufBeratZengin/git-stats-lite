"""Statistics aggregation engine for git history metrics."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .anonymizer import Anonymizer
from .languages import detect_language
from .models import (
    ActivityHeatmap,
    AuthorStats,
    BusFactorAuthor,
    BusFactorResult,
    CommitInfo,
    FileStats,
    LanguageStats,
    RepoReport,
)
from .parser import normalize_email


def count_file_lines(repo_path: str, rel_path: str) -> int:
    """Count lines of a file on disk if it currently exists."""
    full_path = os.path.join(repo_path, rel_path)
    if not os.path.isfile(full_path):
        return 0
    try:
        count = 0
        has_bytes = False
        with open(full_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                has_bytes = True
                count += chunk.count(b"\n")
        return max(1 if has_bytes else 0, count)
    except OSError:
        return 0


def _parse_commit_datetime(iso_str: str, ts: int) -> Tuple[datetime, datetime]:
    """Return (local_dt, utc_dt) from commit ISO timestamp or UNIX epoch."""
    if iso_str:
        try:
            local_dt = datetime.fromisoformat(iso_str)
            # Ensure timezone awareness
            if local_dt.tzinfo is None:
                local_dt = local_dt.replace(tzinfo=timezone.utc)
            utc_dt = local_dt.astimezone(timezone.utc)
            return local_dt, utc_dt
        except Exception:
            pass

    if ts > 0:
        utc_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return utc_dt, utc_dt

    fallback = datetime.now(timezone.utc)
    return fallback, fallback


class AuthorAccumulator:
    """Helper to accumulate metrics for a single author identity."""

    def __init__(self, name: str, canonical_email: str) -> None:
        self.name = name
        self.canonical_email = canonical_email
        self.commits_count = 0
        self.lines_added = 0
        self.lines_deleted = 0
        self.first_date_iso = ""
        self.first_ts = float("inf")
        self.last_date_iso = ""
        self.last_ts = float("-inf")
        self.active_days: Set[str] = set()

    def add_commit(self, dt: datetime, ts: int, iso_str: str, added: int, deleted: int, author_name: str) -> None:
        self.commits_count += 1
        self.lines_added += added
        self.lines_deleted += deleted

        # Keep the latest name or longest non-empty name
        if author_name and (not self.name or len(author_name) > len(self.name)):
            self.name = author_name

        day_key = dt.strftime("%Y-%m-%d")
        self.active_days.add(day_key)

        if ts < self.first_ts:
            self.first_ts = ts
            self.first_date_iso = iso_str or dt.isoformat()

        if ts > self.last_ts:
            self.last_ts = ts
            self.last_date_iso = iso_str or dt.isoformat()


class LanguageAccumulator:
    """Helper to accumulate metrics for a single language."""

    def __init__(self, language: str) -> None:
        self.language = language
        self.files: Set[str] = set()
        self.commits: Set[str] = set()
        self.lines_added = 0
        self.lines_deleted = 0


class FileAccumulator:
    """Helper to accumulate churn per file path."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.commits_count = 0
        self.lines_added = 0
        self.lines_deleted = 0


def calculate_bus_factor(
    commits: List[Tuple[int, str, int]],
    window_months: int,
    author_identities: Dict[str, Tuple[str, str]],
) -> BusFactorResult:
    """Calculate bus factor (minimum authors covering 50% and 80% of lines changed).

    commits list elements: (timestamp, author_key, lines_changed)
    """
    if not commits:
        return BusFactorResult(
            window_months=window_months,
            total_authors_in_window=0,
            total_lines_in_window=0,
            bus_factor_50=0,
            bus_factor_80=0,
        )

    max_ts = max(c[0] for c in commits)
    # Default 30.4375 days per month
    cutoff_ts = max_ts - int(window_months * 30.4375 * 86400) if window_months > 0 else 0

    window_changes: Dict[str, int] = {}
    total_window_lines = 0

    for ts, author_key, lines in commits:
        if ts >= cutoff_ts:
            window_changes[author_key] = window_changes.get(author_key, 0) + lines
            total_window_lines += lines

    # Fallback to all commits if no diffs in window
    if total_window_lines == 0:
        for ts, author_key, lines in commits:
            window_changes[author_key] = window_changes.get(author_key, 0) + lines
            total_window_lines += lines

    if total_window_lines == 0:
        # Fall back to commit counts if all diffs are 0
        for ts, author_key, _ in commits:
            if ts >= cutoff_ts:
                window_changes[author_key] = window_changes.get(author_key, 0) + 1
                total_window_lines += 1

    sorted_authors = sorted(window_changes.items(), key=lambda x: x[1], reverse=True)
    total_authors = len(sorted_authors)

    if total_window_lines == 0 or total_authors == 0:
        return BusFactorResult(
            window_months=window_months,
            total_authors_in_window=total_authors,
            total_lines_in_window=0,
            bus_factor_50=min(1, total_authors),
            bus_factor_80=min(1, total_authors),
        )

    # 50% threshold
    cum_50 = 0
    authors_50: List[BusFactorAuthor] = []
    for key, lines in sorted_authors:
        cum_50 += lines
        pct = (lines / total_window_lines) * 100.0
        name, email = author_identities.get(key, (key, key))
        authors_50.append(BusFactorAuthor(name=name, email=email, lines_changed=lines, percentage=round(pct, 2)))
        if cum_50 >= 0.5 * total_window_lines:
            break
    bus_50 = len(authors_50)

    # 80% threshold
    cum_80 = 0
    authors_80: List[BusFactorAuthor] = []
    for key, lines in sorted_authors:
        cum_80 += lines
        pct = (lines / total_window_lines) * 100.0
        name, email = author_identities.get(key, (key, key))
        authors_80.append(BusFactorAuthor(name=name, email=email, lines_changed=lines, percentage=round(pct, 2)))
        if cum_80 >= 0.8 * total_window_lines:
            break
    bus_80 = len(authors_80)

    return BusFactorResult(
        window_months=window_months,
        total_authors_in_window=total_authors,
        total_lines_in_window=total_window_lines,
        bus_factor_50=bus_50,
        authors_50=authors_50,
        bus_factor_80=bus_80,
        authors_80=authors_80,
    )


class StatsAggregator:
    """Aggregates metrics from a stream of CommitInfo objects."""

    def __init__(
        self,
        repo_name: str = "",
        repo_path: str = ".",
        branch: str = "main",
        bus_factor_months: int = 6,
        anonymizer: Optional[Anonymizer] = None,
        timezone_mode: str = "local",
    ) -> None:
        self.repo_name = repo_name or os.path.basename(os.path.abspath(repo_path))
        self.repo_path = os.path.abspath(repo_path)
        self.branch = branch
        self.bus_factor_months = bus_factor_months
        self.anonymizer = anonymizer
        self.timezone_mode = timezone_mode

        self.authors: Dict[str, AuthorAccumulator] = {}
        self.files: Dict[str, FileAccumulator] = {}
        self.languages: Dict[str, LanguageAccumulator] = {}

        self.grid_local = [[0] * 24 for _ in range(7)]
        self.grid_utc = [[0] * 24 for _ in range(7)]

        self.commits_by_day: Dict[str, int] = {}
        self.commits_by_week: Dict[str, int] = {}

        self.total_commits = 0
        self.total_lines_added = 0
        self.total_lines_deleted = 0
        self.first_commit_date: Optional[str] = None
        self.last_commit_date: Optional[str] = None
        self._min_ts = float("inf")
        self._max_ts = float("-inf")

        self._bus_records: List[Tuple[int, str, int]] = []
        self._all_active_days: Set[str] = set()

    def process_commit(self, commit: CommitInfo) -> None:
        """Process a single commit into all aggregates."""
        self.total_commits += 1

        local_dt, utc_dt = _parse_commit_datetime(commit.author_date_iso, commit.author_timestamp)
        ts = commit.author_timestamp or int(utc_dt.timestamp())

        # Overall timestamps
        if ts < self._min_ts:
            self._min_ts = ts
            self.first_commit_date = commit.author_date_iso or local_dt.isoformat()
        if ts > self._max_ts:
            self._max_ts = ts
            self.last_commit_date = commit.author_date_iso or local_dt.isoformat()

        # Heatmaps (0=Mon .. 6=Sun)
        self.grid_local[local_dt.weekday()][local_dt.hour] += 1
        self.grid_utc[utc_dt.weekday()][utc_dt.hour] += 1

        # Commits by day/week (based on selected timezone_mode)
        active_dt = local_dt if self.timezone_mode == "local" else utc_dt
        day_key = active_dt.strftime("%Y-%m-%d")
        iso_year, iso_week, _ = active_dt.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"

        self.commits_by_day[day_key] = self.commits_by_day.get(day_key, 0) + 1
        self.commits_by_week[week_key] = self.commits_by_week.get(week_key, 0) + 1
        self._all_active_days.add(day_key)

        # Author identity & normalization
        raw_name = commit.author_name.strip()
        raw_email = commit.author_email.strip()
        canonical_email = normalize_email(raw_email)
        author_key = canonical_email if canonical_email else raw_name.lower()

        # Tally lines in this commit
        commit_added = 0
        commit_deleted = 0

        for f in commit.files:
            commit_added += f.additions
            commit_deleted += f.deletions

            # File churn
            if f.path not in self.files:
                self.files[f.path] = FileAccumulator(f.path)
            f_acc = self.files[f.path]
            f_acc.commits_count += 1
            f_acc.lines_added += f.additions
            f_acc.lines_deleted += f.deletions

            # Language breakdown
            lang = detect_language(f.path)
            if lang not in self.languages:
                self.languages[lang] = LanguageAccumulator(lang)
            l_acc = self.languages[lang]
            l_acc.files.add(f.path)
            l_acc.commits.add(commit.hash)
            l_acc.lines_added += f.additions
            l_acc.lines_deleted += f.deletions

        self.total_lines_added += commit_added
        self.total_lines_deleted += commit_deleted

        if author_key not in self.authors:
            self.authors[author_key] = AuthorAccumulator(raw_name, canonical_email)
        self.authors[author_key].add_commit(
            active_dt,
            ts,
            commit.author_date_iso,
            commit_added,
            commit_deleted,
            raw_name,
        )

        commit_changed = commit_added + commit_deleted
        self._bus_records.append((ts, author_key, commit_changed))

    def process_all(self, commits: Iterable[CommitInfo]) -> None:
        """Consume an iterable or generator of commits."""
        for commit in commits:
            self.process_commit(commit)

    def generate_report(self) -> RepoReport:
        """Finalize and compile RepoReport with calculated metrics."""
        total_lines_changed = self.total_lines_added + self.total_lines_deleted

        # Author stats list
        author_list: List[AuthorStats] = []
        author_display_identities: Dict[str, Tuple[str, str]] = {}

        for key, acc in self.authors.items():
            name = acc.name or key
            email = acc.canonical_email or ""

            if self.anonymizer:
                name, email = self.anonymizer.anonymize_author(name, email)
                canonical_email = email
            else:
                canonical_email = acc.canonical_email

            author_display_identities[key] = (name, email)

            l_changed = acc.lines_added + acc.lines_deleted
            pct_commits = (acc.commits_count / self.total_commits * 100.0) if self.total_commits > 0 else 0.0
            pct_lines = (l_changed / total_lines_changed * 100.0) if total_lines_changed > 0 else 0.0

            author_list.append(
                AuthorStats(
                    name=name,
                    email=email,
                    canonical_email=canonical_email,
                    commits_count=acc.commits_count,
                    lines_added=acc.lines_added,
                    lines_deleted=acc.lines_deleted,
                    lines_changed=l_changed,
                    first_commit_date=acc.first_date_iso,
                    last_commit_date=acc.last_date_iso,
                    active_days=len(acc.active_days),
                    percentage_commits=round(pct_commits, 2),
                    percentage_lines=round(pct_lines, 2),
                )
            )

        # Sort authors by commit count descending, then lines changed
        author_list.sort(key=lambda a: (a.commits_count, a.lines_changed), reverse=True)

        # File stats list
        file_list: List[FileStats] = []
        for path, f_acc in self.files.items():
            f_changed = f_acc.lines_added + f_acc.lines_deleted
            # Hotspot score: changes x size on disk if available, else commits x changes
            size_lines = count_file_lines(self.repo_path, path)
            if size_lines > 0:
                hotspot_score = float(f_changed * size_lines)
            else:
                hotspot_score = float(f_acc.commits_count * f_changed)

            file_list.append(
                FileStats(
                    path=path,
                    commits_count=f_acc.commits_count,
                    lines_added=f_acc.lines_added,
                    lines_deleted=f_acc.lines_deleted,
                    lines_changed=f_changed,
                    hotspot_score=round(hotspot_score, 1),
                )
            )

        # Sort files by hotspot score descending, then lines changed
        file_list.sort(key=lambda f: (f.hotspot_score, f.lines_changed), reverse=True)

        # Language stats list
        language_list: List[LanguageStats] = []
        for lang, l_acc in self.languages.items():
            l_changed = l_acc.lines_added + l_acc.lines_deleted
            pct_lines = (l_changed / total_lines_changed * 100.0) if total_lines_changed > 0 else 0.0
            language_list.append(
                LanguageStats(
                    language=lang,
                    files_count=len(l_acc.files),
                    commits_count=len(l_acc.commits),
                    lines_added=l_acc.lines_added,
                    lines_deleted=l_acc.lines_deleted,
                    lines_changed=l_changed,
                    percentage_lines=round(pct_lines, 2),
                )
            )

        # Sort languages by lines changed descending, then files count
        language_list.sort(key=lambda l: (l.lines_changed, l.files_count), reverse=True)

        # Bus Factor
        bus_result = calculate_bus_factor(
            self._bus_records,
            self.bus_factor_months,
            author_display_identities,
        )

        max_local = max((max(row) for row in self.grid_local), default=0)
        max_utc = max((max(row) for row in self.grid_utc), default=0)

        heatmap_local = ActivityHeatmap(
            grid=self.grid_local,
            timezone_mode="local",
            max_val=max_local,
            total_commits=self.total_commits,
        )
        heatmap_utc = ActivityHeatmap(
            grid=self.grid_utc,
            timezone_mode="utc",
            max_val=max_utc,
            total_commits=self.total_commits,
        )

        return RepoReport(
            repo_name=self.repo_name,
            repo_path=self.repo_path,
            branch=self.branch,
            first_commit_date=self.first_commit_date,
            last_commit_date=self.last_commit_date,
            total_commits=self.total_commits,
            total_authors=len(author_list),
            total_files_touched=len(file_list),
            total_lines_added=self.total_lines_added,
            total_lines_deleted=self.total_lines_deleted,
            total_lines_changed=total_lines_changed,
            active_days_count=len(self._all_active_days),
            authors=author_list,
            files=file_list,
            languages=language_list,
            heatmap_local=heatmap_local,
            heatmap_utc=heatmap_utc,
            commits_by_day=dict(sorted(self.commits_by_day.items())),
            commits_by_week=dict(sorted(self.commits_by_week.items())),
            bus_factor=bus_result,
            is_anonymized=self.anonymizer is not None,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
