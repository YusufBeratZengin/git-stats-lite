"""Unit tests for metric aggregation engine and bus factor calculation."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.models import CommitInfo, FileDiff
from git_stats_lite.stats import StatsAggregator, calculate_bus_factor


class TestStats(unittest.TestCase):
    def test_bus_factor_excludes_old_changes(self):
        timestamp = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())
        result = calculate_bus_factor(
            [(timestamp - 400 * 86400, "old", 1000), (timestamp, "recent", 10)],
            window_months=6,
            author_identities={"old": ("Former contributor", "old@example.invalid"),
                               "recent": ("Recent contributor", "recent@example.invalid")},
        )
        self.assertEqual(result.total_lines_in_window, 10)
        self.assertEqual(result.total_authors_in_window, 1)
        self.assertEqual(result.authors_80[0].name, "Recent contributor")

    def test_daily_and_weekly_timezone_boundaries(self):
        date = "2026-01-05T00:30:00+02:00"
        timestamp = int(datetime.fromisoformat(date).timestamp())
        commit = CommitInfo("boundary", "Contributor", "dev@example.invalid", date, timestamp,
                            date, timestamp, "Boundary", [FileDiff("synthetic-demo.py", 2, 1)])
        for mode, day, week in [("local", "2026-01-05", "2026-W02"),
                                ("utc", "2026-01-04", "2026-W01")]:
            with self.subTest(mode=mode):
                aggregator = StatsAggregator(timezone_mode=mode)
                aggregator.process_commit(commit)
                report = aggregator.generate_report()
                self.assertEqual(report.commits_by_day, {day: 1})
                self.assertEqual(report.commits_by_week, {week: 1})
                self.assertEqual(report.first_commit_date, date)
                self.assertEqual(report.last_commit_date, date)

    def test_calculate_bus_factor(self):
        # 100 lines changed total:
        # Contributor A: 60 lines (60%)
        # Contributor B: 25 lines (25%)
        # Contributor C: 15 lines (15%)
        author_map = {
            "alice@example.com": ("Contributor A", "alice@example.com"),
            "bob@example.com": ("Contributor B", "bob@example.com"),
            "charlie@example.com": ("Contributor C", "charlie@example.com"),
        }
        # ts = 1000, inside window
        commits = [
            (1000, "alice@example.com", 60),
            (1000, "bob@example.com", 25),
            (1000, "charlie@example.com", 15),
        ]

        result = calculate_bus_factor(commits, window_months=6, author_identities=author_map)
        self.assertEqual(result.total_authors_in_window, 3)
        self.assertEqual(result.total_lines_in_window, 100)
        # Contributor A has 60% which meets >= 50%
        self.assertEqual(result.bus_factor_50, 1)
        self.assertEqual(len(result.authors_50), 1)
        self.assertEqual(result.authors_50[0].name, "Contributor A")
        self.assertEqual(result.authors_50[0].percentage, 60.0)

        # Contributor A (60%) + Contributor B (25%) = 85% which meets >= 80%
        self.assertEqual(result.bus_factor_80, 2)
        self.assertEqual(len(result.authors_80), 2)
        self.assertEqual(result.authors_80[1].name, "Contributor B")

    def test_noreply_aliasing_aggregation(self):
        agg = StatsAggregator(repo_name="test-repo", repo_path=".", branch="main")

        # Two commits with different email notations from the same GitHub user
        c1 = CommitInfo(
            hash="h1",
            author_name="Contributor A",
            author_email="42+YusufBeratZengin@users.noreply.github.com",
            author_date_iso="2026-05-01T10:00:00Z",
            author_timestamp=1777629600,
            committer_date_iso="2026-05-01T10:00:00Z",
            committer_timestamp=1777629600,
            subject="Commit 1",
            files=[FileDiff(path="app.py", additions=20, deletions=5)],
        )
        c2 = CommitInfo(
            hash="h2",
            author_name="Contributor A",
            author_email="YusufBeratZengin@users.noreply.github.com",
            author_date_iso="2026-05-02T11:00:00Z",
            author_timestamp=1777719600,
            committer_date_iso="2026-05-02T11:00:00Z",
            committer_timestamp=1777719600,
            subject="Commit 2",
            files=[FileDiff(path="app.py", additions=10, deletions=2)],
        )

        agg.process_commit(c1)
        agg.process_commit(c2)
        report = agg.generate_report()

        # Both commits should be grouped under 1 author
        self.assertEqual(report.total_authors, 1)
        self.assertEqual(len(report.authors), 1)
        author = report.authors[0]
        self.assertEqual(author.commits_count, 2)
        self.assertEqual(author.lines_added, 30)
        self.assertEqual(author.lines_deleted, 7)
        self.assertEqual(author.active_days, 2)

    def test_heatmap_coordinates(self):
        agg = StatsAggregator(repo_name="heatmap-test", repo_path=".")
        # 2026-05-04 is a Monday (weekday 0)
        # 14:00 +02:00 -> local hour 14, UTC hour 12
        commit = CommitInfo(
            hash="hm1",
            author_name="Contributor A",
            author_email="alice@example.com",
            author_date_iso="2026-05-04T14:00:00+02:00",
            author_timestamp=1777896000,
            committer_date_iso="2026-05-04T14:00:00+02:00",
            committer_timestamp=1777896000,
            subject="Test heatmap",
            files=[FileDiff(path="file.txt", additions=1, deletions=0)],
        )
        agg.process_commit(commit)
        report = agg.generate_report()

        # Local: Monday (0), hour 14
        self.assertEqual(report.heatmap_local.grid[0][14], 1)
        # UTC: Monday (0), hour 12
        self.assertEqual(report.heatmap_utc.grid[0][12], 1)

    def test_calculate_bus_factor_empty_and_fallback_branches(self):
        # 1. Empty commits
        res_empty = calculate_bus_factor([], window_months=6, author_identities={})
        self.assertEqual(res_empty.total_authors_in_window, 0)
        self.assertEqual(res_empty.total_lines_in_window, 0)
        self.assertEqual(res_empty.bus_factor_50, 0)
        self.assertEqual(res_empty.bus_factor_80, 0)

        # 2. Commits inside window have 0 lines, fallback to older commits with lines
        now_ts = 1770000000
        old_ts = now_ts - (400 * 86400)
        commits_zero_window = [
            (old_ts, "alice", 100),
            (now_ts, "bob", 0),
        ]
        identities = {"alice": ("Alice", "a@example.com"), "bob": ("Bob", "b@example.com")}
        res_fallback_all = calculate_bus_factor(commits_zero_window, window_months=6, author_identities=identities)
        self.assertEqual(res_fallback_all.total_lines_in_window, 100)
        self.assertEqual(res_fallback_all.bus_factor_50, 1)

        # 3. All commits across all history have 0 diff lines (fallback to commit counts)
        commits_all_zero = [
            (now_ts, "alice", 0),
            (now_ts, "bob", 0),
        ]
        res_fallback_commits = calculate_bus_factor(commits_all_zero, window_months=6, author_identities=identities)
        self.assertEqual(res_fallback_commits.total_lines_in_window, 2)
        self.assertEqual(res_fallback_commits.bus_factor_50, 1)

        # 4. Window months = 0 (all history)
        commits_all_hist = [
            (old_ts, "alice", 50),
            (now_ts, "bob", 50),
        ]
        res_all_hist = calculate_bus_factor(commits_all_hist, window_months=0, author_identities=identities)
        self.assertEqual(res_all_hist.total_lines_in_window, 100)
        self.assertEqual(res_all_hist.total_authors_in_window, 2)

    def test_parse_commit_datetime_edge_cases(self):
        from git_stats_lite.stats import _parse_commit_datetime

        # 1. Naive datetime ISO string (no timezone)
        local_dt, _ = _parse_commit_datetime("2026-06-01T10:00:00", 0)
        self.assertIsNotNone(local_dt.tzinfo)
        self.assertEqual(local_dt.tzinfo, timezone.utc)

        # 2. Empty ISO string with positive timestamp
        ts = 1772355600
        local_dt2, _ = _parse_commit_datetime("", ts)
        self.assertEqual(int(local_dt2.timestamp()), ts)

        # 3. Empty ISO string and zero timestamp (fallback)
        local_dt3, _ = _parse_commit_datetime("", 0)
        self.assertIsNotNone(local_dt3.tzinfo)

    def test_count_file_lines(self):
        from unittest.mock import patch

        from git_stats_lite.stats import count_file_lines

        count = count_file_lines(".", "nonexistent_file_path.py")
        self.assertEqual(count, 0)

        with patch("os.path.isfile", return_value=True), patch("builtins.open", side_effect=OSError("Read error")):
            self.assertEqual(count_file_lines(".", "mocked_error.py"), 0)

    def test_author_accumulator_longer_name(self):
        from git_stats_lite.stats import AuthorAccumulator

        acc = AuthorAccumulator("A", "a@example.com")
        acc.add_commit(datetime.now(timezone.utc), 1000, "", 10, 0, "Alice Contributor")
        self.assertEqual(acc.name, "Alice Contributor")

    def test_empty_repository_report(self):
        agg = StatsAggregator(repo_name="empty", repo_path=".")
        report = agg.generate_report()
        self.assertEqual(report.total_commits, 0)
        self.assertEqual(report.total_authors, 0)
        self.assertIsNone(report.first_commit_date)
        self.assertEqual(report.bus_factor.bus_factor_50, 0)

    def test_file_diff_total_changes(self):
        diff = FileDiff(path="module.py", additions=15, deletions=5)
        self.assertEqual(diff.total_changes, 20)


if __name__ == "__main__":
    unittest.main()
