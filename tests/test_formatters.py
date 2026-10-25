"""Unit tests for formatters (Terminal, JSON, Markdown, HTML)."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from git_stats_lite.formatters import (
    format_html_report,
    format_json_report,
    format_markdown_report,
    format_terminal_report,
)
from git_stats_lite.models import (
    ActivityHeatmap,
    AuthorStats,
    BusFactorAuthor,
    BusFactorResult,
    FileStats,
    LanguageStats,
    RepoReport,
)


class TestFormatters(unittest.TestCase):
    def setUp(self):
        self.report = RepoReport(
            repo_name="demo-repo",
            repo_path="/path/to/demo-repo",
            branch="main",
            first_commit_date="2026-01-01T10:00:00Z",
            last_commit_date="2026-05-01T12:00:00Z",
            total_commits=15,
            total_authors=2,
            total_files_touched=3,
            total_lines_added=150,
            total_lines_deleted=30,
            total_lines_changed=180,
            active_days_count=5,
            authors=[
                AuthorStats(
                    name="Contributor A",
                    email="alice@example.com",
                    canonical_email="alice@example.com",
                    commits_count=10,
                    lines_added=120,
                    lines_deleted=20,
                    lines_changed=140,
                    first_commit_date="2026-01-01T10:00:00Z",
                    last_commit_date="2026-05-01T12:00:00Z",
                    active_days=4,
                    percentage_commits=66.67,
                    percentage_lines=77.78,
                ),
                AuthorStats(
                    name="Contributor B",
                    email="bob@example.com",
                    canonical_email="bob@example.com",
                    commits_count=5,
                    lines_added=30,
                    lines_deleted=10,
                    lines_changed=40,
                    first_commit_date="2026-02-01T10:00:00Z",
                    last_commit_date="2026-04-01T12:00:00Z",
                    active_days=2,
                    percentage_commits=33.33,
                    percentage_lines=22.22,
                ),
            ],
            files=[
                FileStats(path="src/main.py", commits_count=8, lines_added=100, lines_deleted=15, lines_changed=115, hotspot_score=1150.0),
                FileStats(path="README.md", commits_count=3, lines_added=20, lines_deleted=5, lines_changed=25, hotspot_score=75.0),
            ],
            languages=[
                LanguageStats(language="Python", files_count=1, commits_count=8, lines_added=100, lines_deleted=15, lines_changed=115, percentage_lines=63.89),
                LanguageStats(language="Markdown", files_count=1, commits_count=3, lines_added=20, lines_deleted=5, lines_changed=25, percentage_lines=13.89),
            ],
            heatmap_local=ActivityHeatmap(grid=[[1] * 24 for _ in range(7)], timezone_mode="local", max_val=1, total_commits=15),
            heatmap_utc=ActivityHeatmap(grid=[[1] * 24 for _ in range(7)], timezone_mode="utc", max_val=1, total_commits=15),
            commits_by_day={"2026-01-01": 5, "2026-05-01": 10},
            commits_by_week={"2026-W01": 5, "2026-W18": 10},
            bus_factor=BusFactorResult(
                window_months=6,
                total_authors_in_window=2,
                total_lines_in_window=180,
                bus_factor_50=1,
                bus_factor_80=2,
                authors_50=[BusFactorAuthor(name="Contributor A", email="alice@example.com", lines_changed=140, percentage=77.8)],
                authors_80=[
                    BusFactorAuthor(name="Contributor A", email="alice@example.com", lines_changed=140, percentage=77.8),
                    BusFactorAuthor(name="Contributor B", email="bob@example.com", lines_changed=40, percentage=22.2),
                ],
            ),
            is_anonymized=False,
            generated_at="2026-05-02T00:00:00Z",
        )

    def test_terminal_report(self):
        text = format_terminal_report(self.report)
        self.assertIn("GIT STATS LITE: demo-repo", text)
        self.assertIn("Total Commits     : 15", text)
        self.assertIn("Bus Factor (50%)  : 1 author(s)", text)
        self.assertIn("Contributor A", text)
        self.assertIn("Python", text)
        self.assertIn("src/main.py", text)

    def test_json_report(self):
        json_str = format_json_report(self.report)
        data = json.loads(json_str)
        self.assertEqual(data["repo_name"], "demo-repo")
        self.assertEqual(data["total_commits"], 15)
        self.assertEqual(data["bus_factor"]["bus_factor_50"], 1)
        self.assertEqual(len(data["authors"]), 2)
        self.assertEqual(len(data["languages"]), 2)

    def test_markdown_report(self):
        md = format_markdown_report(self.report)
        self.assertIn("# Git Stats Lite: demo-repo", md)
        self.assertIn("## Repository Overview", md)
        self.assertIn("## Bus Factor", md)
        self.assertIn("| Contributor A |", md)
        self.assertIn("| Python |", md)

    def test_html_report_self_contained(self):
        html_out = format_html_report(self.report)
        self.assertIn("<!DOCTYPE html>", html_out)
        self.assertIn("<svg", html_out)
        self.assertIn("heatmap-svg", html_out)
        self.assertIn("timeline-svg", html_out)
        self.assertIn("author-svg", html_out)
        self.assertIn("lang-bar-svg", html_out)
        self.assertIn("prefers-color-scheme: dark", html_out)
        self.assertIn("Date range: 2026-01-01 to 2026-05-01", html_out)

        # Zero external scripts, fonts or cdns
        self.assertNotIn("http://", html_out)
        self.assertNotIn("https://", html_out)
        self.assertNotIn("<script src=", html_out)
        self.assertNotIn("<link rel=\"stylesheet\" href=", html_out)

    def test_format_table_empty(self):
        from git_stats_lite.formatters.terminal import _format_table

        self.assertEqual(_format_table([], [], []), "")

    def test_empty_report_formatters(self):
        empty_report = RepoReport(
            repo_name="empty-repo",
            repo_path="/path/to/empty",
            branch="main",
            first_commit_date=None,
            last_commit_date=None,
            total_commits=0,
            total_authors=0,
            total_files_touched=0,
            total_lines_added=0,
            total_lines_deleted=0,
            total_lines_changed=0,
            active_days_count=0,
            authors=[],
            files=[],
            languages=[],
            heatmap_local=ActivityHeatmap(grid=[[0] * 24 for _ in range(7)], timezone_mode="local", max_val=0, total_commits=0),
            heatmap_utc=ActivityHeatmap(grid=[[0] * 24 for _ in range(7)], timezone_mode="utc", max_val=0, total_commits=0),
            commits_by_day={},
            commits_by_week={},
            bus_factor=BusFactorResult(0, 0, 0, 0, 0, [], []),
            is_anonymized=False,
            generated_at="2026-05-02T00:00:00Z",
        )

        term = format_terminal_report(empty_report)
        self.assertIn("No authors found.", term)
        self.assertIn("No file diffs detected.", term)
        self.assertIn("No modified files recorded.", term)

        html = format_html_report(empty_report)
        self.assertIn("No timeline activity to display.", html)
        self.assertIn("No authors found.", html)
        self.assertIn("No languages detected.", html)

        md = format_markdown_report(empty_report)
        self.assertIn("# Git Stats Lite: empty-repo", md)

        js = format_json_report(empty_report)
        self.assertIn('"total_commits": 0', js)

    def test_html_heatmap_level_shading(self):
        from git_stats_lite.formatters.html import _generate_svg_heatmap

        # Create a heatmap with varying values to hit levels 1, 2, 3, 4
        # max_val = 100:
        # ratio 0.20 -> level 1
        # ratio 0.40 -> level 2
        # ratio 0.70 -> level 3
        # ratio 0.90 -> level 4
        grid = [[0] * 24 for _ in range(7)]
        grid[0][1] = 20
        grid[0][2] = 40
        grid[0][3] = 70
        grid[0][4] = 90
        hm = ActivityHeatmap(grid=grid, timezone_mode="utc", max_val=100, total_commits=220)
        svg = _generate_svg_heatmap(hm)
        self.assertIn("heat-1", svg)
        self.assertIn("heat-2", svg)
        self.assertIn("heat-3", svg)
        self.assertIn("heat-4", svg)


if __name__ == "__main__":
    unittest.main()
