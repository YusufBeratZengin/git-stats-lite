"""Example demonstrating multi-format exports (HTML, Markdown, JSON, Terminal) via Python API."""

import sys
from pathlib import Path

# Add src to sys.path for direct execution from checkout
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from git_stats_lite.anonymizer import Anonymizer
from git_stats_lite.formatters import (
    format_html_report,
    format_json_report,
    format_markdown_report,
    format_terminal_report,
)
from git_stats_lite.parser import parse_git_log_stream
from git_stats_lite.stats import StatsAggregator


def main() -> None:
    # Deterministic synthetic git log lines for demonstration
    synthetic_log = [
        "@@@COMMIT@@@\x00c101\x00Alice Contributor\x00alice@example.invalid\x002026-03-01T09:00:00+00:00\x001772355600\x002026-03-01T09:00:00+00:00\x001772355600\x00feat: initial project structure",
        "120\t0\tsrc/core.py",
        "45\t0\tsrc/utils.py",
        "25\t0\tREADME.md",
        "@@@COMMIT@@@\x00c102\x00Bob Contributor\x00bob@example.invalid\x002026-03-02T14:30:00+00:00\x001772461800\x002026-03-02T14:30:00+00:00\x001772461800\x00feat: add parser engine",
        "85\t10\tsrc/parser.py",
        "15\t5\tsrc/core.py",
        "@@@COMMIT@@@\x00c103\x00Charlie Contributor\x00charlie@example.invalid\x002026-03-03T18:00:00+00:00\x001772560800\x002026-03-03T18:00:00+00:00\x001772560800\x00docs: update usage guide",
        "30\t5\tREADME.md",
    ]

    # Initialize aggregator with privacy anonymization enabled
    aggregator = StatsAggregator(
        repo_name="sample-project",
        repo_path="sample-project",
        branch="main",
        anonymizer=Anonymizer(),
        timezone_mode="utc",
    )
    aggregator.process_all(parse_git_log_stream(synthetic_log))
    report = aggregator.generate_report()

    # 1. Summary metrics
    print(f"Project: {report.repo_name}")
    print(f"Total Commits: {report.total_commits} across {report.active_days_count} active days")
    print(f"Contributors: {report.total_authors} (anonymized)")
    print(f"Lines Changed: +{report.total_lines_added} / -{report.total_lines_deleted}")
    print(f"Bus Factor (50%): {report.bus_factor.bus_factor_50}")

    # 2. Terminal report string (first 100 characters preview)
    terminal_output = format_terminal_report(report, top_n=5, timezone_mode="utc")
    print(f"\nGenerated Terminal report: {len(terminal_output)} characters")

    # 2. Structured JSON
    json_output = format_json_report(report)
    print(f"\nGenerated JSON report: {len(json_output)} bytes")

    # 3. GitHub Flavored Markdown
    md_output = format_markdown_report(report, top_n=5)
    print(f"Generated Markdown report: {len(md_output.splitlines())} lines")

    # 4. Standalone self-contained HTML report with inline SVG charts
    html_output = format_html_report(report, top_n=5)
    print(f"Generated standalone HTML report: {len(html_output)} bytes")


if __name__ == "__main__":
    main()
