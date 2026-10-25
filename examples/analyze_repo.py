"""Example demonstrating programmatic analysis of a local git repository."""

import sys
from pathlib import Path

# Add src to sys.path for direct execution from checkout
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from git_stats_lite.git import (
    get_current_branch,
    is_git_available,
    is_git_repository,
    stream_git_log,
)
from git_stats_lite.parser import parse_git_log_stream
from git_stats_lite.stats import StatsAggregator


def main() -> None:
    repo_target = sys.argv[1] if len(sys.argv) > 1 else "."

    if not is_git_available():
        print("Git executable not found in PATH.", file=sys.stderr)
        sys.exit(1)

    if not is_git_repository(repo_target):
        print(f"Path '{repo_target}' is not a valid git repository.", file=sys.stderr)
        sys.exit(1)

    branch = get_current_branch(repo_target) or "HEAD"

    # Stream and aggregate commits from the last 1 year
    log_stream = stream_git_log(repo_target, since="1y")
    aggregator = StatsAggregator(repo_path=repo_target, branch=branch, timezone_mode="local")
    aggregator.process_all(parse_git_log_stream(log_stream))
    report = aggregator.generate_report()

    print(f"Repository   : {report.repo_name}")
    print(f"Branch       : {report.branch}")
    print(f"Commits      : {report.total_commits}")
    print(f"Authors      : {report.total_authors}")
    print(f"Files        : {report.total_files_touched}")
    print(f"Lines (+/-)  : +{report.total_lines_added:,} / -{report.total_lines_deleted:,}")
    print(f"Bus Factor   : 50%={report.bus_factor.bus_factor_50}, 80%={report.bus_factor.bus_factor_80}")

    if report.languages:
        top_lang = report.languages[0]
        print(f"Top Language : {top_lang.language} ({top_lang.percentage_lines:.1f}% lines)")


if __name__ == "__main__":
    main()
