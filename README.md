# git-stats-lite

[![CI](https://github.com/YusufBeratZengin/git-stats-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/YusufBeratZengin/git-stats-lite/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/git-stats-lite.svg)](https://pypi.org/project/git-stats-lite/)
[![Python Version](https://img.shields.io/badge/python-%3E%3D3.10-3776ab.svg?logo=python&logoColor=white)](https://pypi.org/project/git-stats-lite/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)](pyproject.toml)

> Fast, private repository statistics and bus factor insights from local git history.

[English](README.md) | [Türkçe](README.tr.md)

## Demo

<p align="center">
  <img src="docs/demo.svg" alt="git-stats-lite terminal demo" width="720">
</p>

## Why git-stats-lite?

- **Zero runtime dependencies & 100% offline**: Runs entirely against your local git clone via native subprocess streaming. No network calls, no cloud services, no tracking, and no external libraries required.
- **Actionable health & bus factor metrics**: Computes 50% and 80% bus factor risk windows, identifies code churn hotspots (`changes * size`), and maps 7x24 weekday-hour activity patterns in author local time or UTC.
- **Multi-format portable exports**: Generates terminal tables, machine-readable JSON, GitHub Flavored Markdown, and standalone single-file HTML reports with self-contained, responsive inline SVG charts (light and dark mode supported).

## Install

Run instantly from your checkout with Python 3.10+ (no package installation required):

```sh
# Clone and analyze right away
git clone https://github.com/YusufBeratZengin/git-stats-lite.git
cd git-stats-lite
python src/git_stats_lite/cli.py . --top 5
```

The package is not yet published on PyPI. Install locally with pip from the checkout:

```sh
python -m pip install .
git-stats . --top 5
```

## Usage

### Command Line Interface

```sh
# Analyze the last 1 year with author privacy anonymization
git-stats . --since 1y --anonymize

# Export to standalone single-file HTML with interactive SVG charts
git-stats . --html report.html

# Export to Markdown summary and raw JSON data
git-stats . --markdown summary.md --json stats.json

# View activity heatmap in UTC timezone
git-stats . --tz utc --top 5

# Analyze a specific branch or revision
git-stats . --branch main --since 6m
```

> **Tip:** You can run `python src/git_stats_lite/cli.py` or `python -m git_stats_lite` directly before installing.

### Python API

```python
from git_stats_lite.git import stream_git_log
from git_stats_lite.parser import parse_git_log_stream
from git_stats_lite.stats import StatsAggregator

# Aggregate metrics from git history stream
stats = StatsAggregator(repo_path=".", timezone_mode="utc")
stats.process_all(parse_git_log_stream(stream_git_log(".", since="1y")))
report = stats.generate_report()

print(f"Total Commits: {report.total_commits}")
print(f"Bus Factor (50%): {report.bus_factor.bus_factor_50}")
```

## Configuration

| Option | Description | Default |
| --- | --- | --- |
| `path` | Repository path or subdirectory | `.` |
| `--since DATE`, `--until DATE` | ISO dates (e.g., `2026-01-01`) or non-negative intervals (`y`, `m`, `w`, `d`, `h`; e.g., `1y`, `6m`, `30d`) | `None` |
| `--branch REV`, `--rev REV` | Branch, tag, or revision to inspect | Active branch |
| `--all` | Include all refs in analysis | `false` |
| `--format {terminal,json,markdown,html}` | Primary output format | `terminal` |
| `-o FILE`, `--output FILE` | Write primary output to destination file | stdout |
| `--html [FILE]` | Generate self-contained HTML report (to file or stdout) | `None` |
| `--json [FILE]` | Export structured JSON data (to file or stdout) | `None` |
| `--markdown [FILE]`, `--md [FILE]` | Export GitHub Flavored Markdown summary | `None` |
| `--anonymize` | Pseudonymize contributor names and emails with SHA-256 | `false` |
| `--bus-factor-months N` | Non-negative time window in months for bus factor analysis (`0` = all history) | `6` |
| `--top N` | Positive number of rows to display in summary tables | `10` |
| `--tz {local,utc}` | Timezone calculation mode for 7x24 activity heatmap | `local` |
| `--mailmap FILE` | Path to additional custom mailmap mapping file | `None` |
| `--version`, `-h`, `--help` | Display version or help message | |

## FAQ & Limitations

- **How is the Bus Factor calculated?**
  The bus factor window defaults to the most recent 6 months ending at the latest analyzed commit. Contributors are ranked by changed lines (additions + deletions). The bus factor represents the minimal set of contributors responsible for 50% and 80% of lines churned. If all diffs are zero, it gracefully falls back to commit counts.
- **What does `--anonymize` do and what are its boundaries?**
  Author names and email addresses are pseudonymized using deterministic salted SHA-256 hashes (`Author-xxxxxxxx`). While personal names and emails are masked, repo metadata, file paths, and commit timestamps remain visible.
- **What timezone is used for heatmaps?**
  In `--tz local` mode, each commit uses the local timezone recorded by Git when the commit was authored. In `--tz utc` mode, timestamps are converted to UTC for global team comparison.
- **Does it work on shallow clones?**
  Yes, but statistics reflect only the fetched history depth. For complete history, ensure `git fetch --unshallow` is run first.

## Contributing

Contributions, bug reports, and suggestions are welcome!
Please review [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md).

For development:

```sh
# Clone repository and install dev dependencies
python -m pip install -e ".[dev]"

# Run linter, typecheck, and test suite with coverage
python -m ruff check .
python -m mypy src
python -m pytest
```

## License

[MIT](LICENSE). Copyright (c) 2026 Yusuf Berat Zengin.
