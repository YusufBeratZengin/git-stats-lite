"""Unit tests for metric aggregation engine and bus factor calculation."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.models import CommitInfo, FileDiff
from git_stats_lite.stats import StatsAggregator, calculate_bus_factor


class TestStats(unittest.TestCase):
    def test_calculate_bus_factor(self):
        # 100 lines changed total:
        # Alice: 60 lines (60%)
        # Bob: 25 lines (25%)
        # Charlie: 15 lines (15%)
        author_map = {
            "alice@example.com": ("Alice", "alice@example.com"),
            "bob@example.com": ("Bob", "bob@example.com"),
            "charlie@example.com": ("Charlie", "charlie@example.com"),
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
        # Alice has 60% which meets >= 50%
        self.assertEqual(result.bus_factor_50, 1)
        self.assertEqual(len(result.authors_50), 1)
        self.assertEqual(result.authors_50[0].name, "Alice")
        self.assertEqual(result.authors_50[0].percentage, 60.0)

        # Alice (60%) + Bob (25%) = 85% which meets >= 80%
        self.assertEqual(result.bus_factor_80, 2)
        self.assertEqual(len(result.authors_80), 2)
        self.assertEqual(result.authors_80[1].name, "Bob")

    def test_noreply_aliasing_aggregation(self):
        agg = StatsAggregator(repo_name="test-repo", repo_path=".", branch="main")

        # Two commits with different email notations from the same GitHub user
        c1 = CommitInfo(
            hash="h1",
            author_name="Yusuf Berat Zengin",
            author_email="118852217+YusufBeratZengin@users.noreply.github.com",
            author_date_iso="2026-05-01T10:00:00Z",
            author_timestamp=1777629600,
            committer_date_iso="2026-05-01T10:00:00Z",
            committer_timestamp=1777629600,
            subject="Commit 1",
            files=[FileDiff(path="app.py", additions=20, deletions=5)],
        )
        c2 = CommitInfo(
            hash="h2",
            author_name="Yusuf Berat Zengin",
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
            author_name="Alice",
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


if __name__ == "__main__":
    unittest.main()
