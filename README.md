# git-stats-lite
[![CI](https://github.com/YusufBeratZengin/git-stats-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/YusufBeratZengin/git-stats-lite/actions/workflows/ci.yml) [![PyPI](https://img.shields.io/pypi/v/git-stats-lite)](https://pypi.org/project/git-stats-lite/) [![MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE) ![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Dependencies](https://img.shields.io/badge/runtime_dependencies-0-green)

Local Git history statistics: activity, authors, churn, languages, and bus factor.
Runs offline with zero runtime dependencies; includes a self-contained HTML report.
From a source checkout: `python -m pip install .`
Try it: `python src/git_stats_lite/cli.py . --since 1y --anonymize`

[English](README.md) | [Türkçe](README.tr.md)

## Features

- Streaming `git log --numstat` parsing with `.mailmap` and noreply alias normalization.
- Daily/weekly commit counts, 7x24 weekday-hour heatmaps in author local time or UTC, first/last dates.
- Author totals, file churn and hotspots, language breakdown by extension and special filename.
- Minimum authors covering 50%/80% of changed lines in a configurable bus factor window.
- Terminal, JSON, Markdown, and single-file HTML with inline SVG and automatic light/dark themes.
- `--anonymize` replaces author names/emails with deterministic SHA-256 pseudonyms.

## Demo

Actual output from the synthetic offline example:

```sh
python examples/demo.py
```

```text
Commits: 2; authors: 2
Lines: +12 / -3
Language: Python
Bus factor: 50%=1, 80%=2
UTC activity: Monday 10:00=1, Tuesday 12:00=1
```

## Install

Requires Python 3.10+ and Git on PATH. From a source checkout:

```sh
python -m pip install .
```

This is a source installation; the PyPI badge reflects any published release.
The installed commands are `git-stats` and `git-stats-lite`.
You can also run `python src/git_stats_lite/cli.py` directly from the checkout.

## Usage

```sh
python src/git_stats_lite/cli.py . --since 1y --anonymize
python src/git_stats_lite/cli.py . --tz utc --format json --anonymize
python src/git_stats_lite/cli.py . --anonymize --html is/report.html
python src/git_stats_lite/cli.py . --anonymize --markdown is/summary.md
```

Create the output directory before exporting. After installation, replace
`python src/git_stats_lite/cli.py` with `git-stats` or `python -m git_stats_lite`.

Python API (after installation):

```python
from git_stats_lite.git import stream_git_log
from git_stats_lite.parser import parse_git_log_stream
from git_stats_lite.stats import StatsAggregator

stats = StatsAggregator(repo_path=".", timezone_mode="utc")
stats.process_all(parse_git_log_stream(stream_git_log(".", since="1y")))
report = stats.generate_report()
print(report.total_commits)
```

## Examples

[examples/demo.py](examples/demo.py) feeds synthetic log records through the actual
parser and aggregator. It needs no installation, network, or Git history changes.

## Configuration / options

| Option | Description |
| --- | --- |
| `path` | Repository or subdirectory; default `.` |
| `--since DATE`, `--until DATE` | Git dates or intervals such as `1y`, `6m`; `m` means months |
| `--branch REV`, `--rev REV` | Branch, tag, or revision |
| `--all` | Include all refs |
| `--format {terminal,json,markdown,html}` | Primary format; default terminal (choose one value) |
| `-o FILE`, `--output FILE` | Save primary output |
| `--html [FILE]`, `--json [FILE]` | Export to a file, or stdout without FILE |
| `--markdown [FILE]`, `--md [FILE]` | Markdown export |
| `--anonymize` | Hash author names and emails |
| `--bus-factor-months N` | Window in months; default 6, 0 means all history |
| `--top N` | Table row limit; default 10 |
| `--tz {local,utc}` | Activity timezone; default local (choose one value) |
| `--mailmap FILE` | Additional custom mailmap |
| `--version`, `-h`, `--help` | Version or help |

## How it works

Git applies the repository mailmap, then the parser applies an optional custom
mailmap. Metrics accumulate while log records stream through the parser.
Memory grows with authors, files, days, and compact per-commit bus factor records.
Hotspots use changed lines * current working-tree line count; missing or empty
files fall back to commit count * changed lines. Languages describe history churn,
not the current source tree. Reports require no external assets or JavaScript libraries.

## Limitations / privacy

"Local" means each author's recorded timezone, not the viewer's timezone.
The bus factor window ends at the newest analyzed commit and approximates each
month as 30.4375 days. If its window has no changed lines, it falls back to all
analyzed changes, then commit counts when all diffs are zero. Binary diffs count
as zero lines. Merge diffs follow Git's default log behavior.

No repository data is sent over the network. Pseudonyms use a fixed salt and are
linkable across reports; hashing does not guarantee anonymity. Repository names,
absolute paths, branches, and file paths remain visible with `--anonymize`.
Review every exported report before sharing. Use synthetic repositories in bug reports.

## Development

```sh
python -m pip install -e ".[dev]"
python -m ruff check .
python -m mypy src
python -m pytest -q
python -m build
python -m twine check dist/*
```

CI checks Python 3.10-3.13 on Windows and Linux. Tests run offline with scripted
commits in temporary repositories. Build tools are development dependencies only.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md),
and [SECURITY.md](SECURITY.md). Release automation uses PyPI trusted publishing;
a maintainer must configure the publisher and protected `pypi` environment first.

## License

[MIT](LICENSE). Copyright (c) 2026 Yusuf Berat Zengin.
