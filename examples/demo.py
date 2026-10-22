"""Run a deterministic, offline example using synthetic Git log records."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from git_stats_lite.anonymizer import Anonymizer
from git_stats_lite.parser import parse_git_log_stream
from git_stats_lite.stats import StatsAggregator


def main() -> None:
    lines = [
        "@@@COMMIT@@@\x00demo1\x00Contributor A\x00a@example.invalid\x002026-01-05T10:00:00+00:00\x001767607200\x002026-01-05T10:00:00+00:00\x001767607200\x00Add module",
        "10\t0\tsynthetic-demo.py",
        "@@@COMMIT@@@\x00demo2\x00Contributor B\x00b@example.invalid\x002026-01-06T12:00:00+00:00\x001767700800\x002026-01-06T12:00:00+00:00\x001767700800\x00Edit module",
        "2\t3\tsynthetic-demo.py",
    ]
    aggregator = StatsAggregator(repo_name="synthetic-demo", anonymizer=Anonymizer())
    aggregator.process_all(parse_git_log_stream(lines))
    report = aggregator.generate_report()
    print(f"Commits: {report.total_commits}; authors: {report.total_authors}")
    print(f"Lines: +{report.total_lines_added} / -{report.total_lines_deleted}")
    print(f"Language: {report.languages[0].language}")
    print(f"Bus factor: 50%={report.bus_factor.bus_factor_50}, 80%={report.bus_factor.bus_factor_80}")
    print(f"UTC activity: Monday 10:00={report.heatmap_utc.grid[0][10]}, Tuesday 12:00={report.heatmap_utc.grid[1][12]}")


if __name__ == "__main__":
    main()
