"""Command-line interface for git-stats-lite."""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from git_stats_lite import __version__
    from git_stats_lite.anonymizer import Anonymizer
    from git_stats_lite.formatters import (
        format_html_report,
        format_json_report,
        format_markdown_report,
        format_terminal_report,
    )
    from git_stats_lite.git import (
        GitError,
        get_current_branch,
        get_repo_root,
        is_git_available,
        is_git_repository,
        stream_git_log,
    )
    from git_stats_lite.parser import MailmapLookup, parse_git_log_stream
    from git_stats_lite.stats import StatsAggregator
else:
    from . import __version__
    from .anonymizer import Anonymizer
    from .formatters import (
        format_html_report,
        format_json_report,
        format_markdown_report,
        format_terminal_report,
    )
    from .git import (
        GitError,
        get_current_branch,
        get_repo_root,
        is_git_available,
        is_git_repository,
        stream_git_log,
    )
    from .parser import MailmapLookup, parse_git_log_stream
    from .stats import StatsAggregator


def _is_valid_date(value: str) -> bool:
    """Accept interval shorthand or an ISO calendar date with optional time."""
    if re.fullmatch(r"[0-9]+[ymwdh]", value):
        return True
    if not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}"
        r"(?:[T ][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]+)?)?"
        r"(?:Z|[+-][0-9]{2}:[0-9]{2})?)?",
        value,
    ):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _non_negative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return number


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="git-stats",
        description="Fast, private repository statistics from local git history.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to git repository or working tree directory.",
    )

    parser.add_argument(
        "--since",
        metavar="DATE",
        help="Show commits more recent than an ISO date or interval (e.g. '1y', '6m', '2024-01-01').",
    )

    parser.add_argument(
        "--until",
        metavar="DATE",
        help="Show commits older than an ISO date or interval (e.g. '2024-01-01', '30d').",
    )

    parser.add_argument(
        "--branch",
        "--rev",
        dest="revision",
        metavar="REV",
        help="Target branch, tag, or revision (e.g. 'main', 'HEAD').",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Include commits across all refs/branches.",
    )

    parser.add_argument(
        "--format",
        choices=["terminal", "json", "markdown", "html"],
        default="terminal",
        help="Primary output format to display on stdout or target destination.",
    )

    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="File path to write primary report output.",
    )

    parser.add_argument(
        "--html",
        nargs="?",
        const=True,
        default=None,
        metavar="FILE",
        help="Generate standalone HTML report. If FILE is specified, saves report to that file.",
    )

    parser.add_argument(
        "--json",
        nargs="?",
        const=True,
        default=None,
        metavar="FILE",
        help="Output structured JSON. If FILE is specified, saves JSON to that file.",
    )

    parser.add_argument(
        "--markdown",
        "--md",
        nargs="?",
        const=True,
        default=None,
        metavar="FILE",
        help="Output Markdown report. If FILE is specified, saves Markdown to that file.",
    )

    parser.add_argument(
        "--anonymize",
        action="store_true",
        help="Privacy mode: deterministically hashes author names and emails with SHA-256.",
    )

    parser.add_argument(
        "--bus-factor-months",
        type=_non_negative_int,
        default=6,
        metavar="N",
        help="Evaluation window in months for bus factor calculation (0 for entire history).",
    )

    parser.add_argument(
        "--top",
        type=_positive_int,
        default=10,
        metavar="N",
        help="Number of top authors, files, and languages to display in tables.",
    )

    parser.add_argument(
        "--tz",
        choices=["local", "utc"],
        default="local",
        help="Timezone for activity heatmap and commit metrics.",
    )

    parser.add_argument(
        "--mailmap",
        metavar="FILE",
        help="Optional path to custom .mailmap file for author normalization.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI main execution function."""
    parser = build_parser()
    args = parser.parse_args(argv)

    for option in ("since", "until"):
        value = getattr(args, option)
        if value is not None and not _is_valid_date(value):
            parser.error(f"invalid --{option} value '{value}'")

    if not is_git_available():
        sys.stderr.write("Error: 'git' executable was not found in PATH.\n")
        return 1

    target_path = os.path.abspath(args.path)
    if not os.path.exists(target_path):
        sys.stderr.write(f"Error: Target path does not exist: {args.path}\n")
        return 1

    if not is_git_repository(target_path):
        sys.stderr.write(f"Error: '{args.path}' is not inside a git repository.\n")
        return 1

    try:
        repo_root = get_repo_root(target_path)
    except GitError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1

    branch = args.revision or get_current_branch(repo_root)

    # Load custom mailmap if provided
    mailmap = None
    if args.mailmap:
        mailmap_path = os.path.abspath(args.mailmap)
        if os.path.isfile(mailmap_path):
            mailmap = MailmapLookup.from_file(mailmap_path)
        else:
            sys.stderr.write(f"Warning: Specified mailmap file '{args.mailmap}' does not exist.\n")

    anonymizer = Anonymizer() if args.anonymize else None

    # Stream git log lines and parse commits
    try:
        raw_lines = stream_git_log(
            repo_path=repo_root,
            since=args.since,
            until=args.until,
            revision=args.revision,
            all_branches=args.all,
        )
        commits_stream = parse_git_log_stream(raw_lines, mailmap=mailmap)

        aggregator = StatsAggregator(
            repo_name=os.path.basename(repo_root),
            repo_path=repo_root,
            branch=branch,
            bus_factor_months=args.bus_factor_months,
            anonymizer=anonymizer,
            timezone_mode=args.tz,
        )
        aggregator.process_all(commits_stream)
        report = aggregator.generate_report()

    except GitError as e:
        sys.stderr.write(f"Git error: {e}\n")
        return 1
    except Exception as e:  # noqa: BLE001 -- CLI boundary reports analysis failures to the user.
        sys.stderr.write(f"Error: Unexpected error during analysis: {e}\n")
        return 1

    # Check if empty repo and default terminal format requested
    if report.total_commits == 0 and args.format == "terminal" and not args.output and not args.html and not args.json and not args.markdown:
        sys.stdout.write(f"Repository at '{repo_root}' has no commits matching the criteria.\n")
        return 0

    # Handle dedicated file exports if flags like --html <file>, --json <file>, --markdown <file> are used
    saved_files: list[str] = []

    if isinstance(args.html, str):
        html_out = format_html_report(report, top_n=args.top, timezone_mode=args.tz)
        try:
            with open(args.html, "w", encoding="utf-8") as f:
                f.write(html_out)
            saved_files.append(f"HTML report saved to: {args.html}")
        except OSError as e:
            sys.stderr.write(f"Error: Failed to write HTML output to '{args.html}': {e}\n")
            return 1

    if isinstance(args.json, str):
        json_out = format_json_report(report)
        try:
            with open(args.json, "w", encoding="utf-8") as f:
                f.write(json_out + "\n")
            saved_files.append(f"JSON data saved to: {args.json}")
        except OSError as e:
            sys.stderr.write(f"Error: Failed to write JSON output to '{args.json}': {e}\n")
            return 1

    if isinstance(args.markdown, str):
        md_out = format_markdown_report(report, top_n=args.top, timezone_mode=args.tz)
        try:
            with open(args.markdown, "w", encoding="utf-8") as f:
                f.write(md_out + "\n")
            saved_files.append(f"Markdown report saved to: {args.markdown}")
        except OSError as e:
            sys.stderr.write(f"Error: Failed to write Markdown output to '{args.markdown}': {e}\n")
            return 1

    # Determine primary format output
    effective_format = args.format
    if args.json is True:
        effective_format = "json"
    elif args.markdown is True:
        effective_format = "markdown"
    elif args.html is True and not isinstance(args.html, str):
        effective_format = "html"

    if effective_format == "json":
        primary_output = format_json_report(report)
    elif effective_format == "markdown":
        primary_output = format_markdown_report(report, top_n=args.top, timezone_mode=args.tz)
    elif effective_format == "html":
        primary_output = format_html_report(report, top_n=args.top, timezone_mode=args.tz)
    else:
        primary_output = format_terminal_report(report, top_n=args.top, timezone_mode=args.tz)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(primary_output)
                if not primary_output.endswith("\n"):
                    f.write("\n")
        except OSError as e:
            sys.stderr.write(f"Error: Failed to write primary output to '{args.output}': {e}\n")
            return 1
    else:
        sys.stdout.write(primary_output)
        if not primary_output.endswith("\n"):
            sys.stdout.write("\n")

    for msg in saved_files:
        sys.stderr.write(f"{msg}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
