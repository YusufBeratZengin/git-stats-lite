# git-stats-lite

Fast, private repository statistics from local git history with zero runtime dependencies.

`git-stats-lite` analyzes local git repositories using streaming subprocess calls to `git log --numstat`, extracting activity heatmaps, contributor statistics, file churn hotspots, language distributions, and bus factor metrics without sending any data over the network or relying on third-party libraries.

[Türkçe Dokümantasyon (README.tr.md)](README.tr.md)

---

## Features

- **Zero Runtime Dependencies:** Pure Python standard library implementation. Requires Python >= 3.10 and a standard `git` binary.
- **Streaming Log Parsing:** Reads `git log --numstat` directly from standard output in a streaming fashion. Operates in constant memory regardless of commit depth.
- **Author Identity Normalization:**
  - Built-in `.mailmap` support via `git log --use-mailmap` and custom mailmap parsing.
  - Automatic normalization of GitHub (`<id>+<user>@users.noreply.github.com`) and GitLab noreply aliases to canonical identities.
- **Activity Heatmap:** 7x24 weekday-hour distribution matrix computed in both author local timezones and UTC.
- **File Churn and Hotspots:** Measures additions, deletions, modification counts, and computes hotspot ranking scores (`changes * size`).
- **Language Breakdown:** Classifies files and line diffs by programming language using file extension mapping and special filename detection (e.g. `Dockerfile`, `Makefile`).
- **Bus Factor Analysis:** Calculates the minimum number of authors responsible for 50% and 80% of lines changed in the repository over a configurable rolling time window (default: 6 months).
- **Privacy Mode (`--anonymize`):** Deterministically pseudonymizes author names and emails using salted SHA-256 hashes (`Author-xxxxxxxx`, `anon-xxxxxxxx@privacy.local`), ensuring reports can be shared publicly without leaking identity.
- **Multi-Format Output:**
  - Terminal: Formatted Unicode/ASCII tables with an ASCII activity matrix.
  - JSON: Machine-readable structured payload.
  - Markdown: GitHub Flavored Markdown report.
  - HTML: Fully standalone, single-file HTML report featuring responsive inline SVG charts (heatmap, commit timeline, author breakdown, language distribution) with automated light and dark mode support. No external fonts, styles, or JavaScript libraries required.

---

## Requirements

- Python >= 3.10
- Git >= 2.0

---

## Installation

Install using `pip` from source:

```bash
pip install .
```

Or run directly without installation using Python:

```bash
python -m git_stats_lite.cli [path] [options]
```

---

## Usage Examples

### Terminal Overview

Analyze the current repository:

```bash
git-stats
```

Analyze a specific repository path:

```bash
git-stats /path/to/repository
```

### Time Filters

Filter commits from the last year or within a date range:

```bash
git-stats --since 1y
git-stats --since 2025-01-01 --until 2025-12-31
```

### Self-Contained HTML Report

Generate a standalone HTML report with inline SVG charts:

```bash
git-stats --html report.html
```

Or write directly to an output destination:

```bash
git-stats --format html -o report.html
```

### JSON and Markdown Export

Generate structured JSON data for automated pipelines:

```bash
git-stats --json stats.json
```

Generate Markdown summary for documentation or CI summaries:

```bash
git-stats --markdown summary.md
```

### Privacy Mode

Sanitize all author identities before exporting:

```bash
git-stats --anonymize --html public-report.html
```

### Custom Bus Factor Window

Calculate bus factor based on lines changed over the last 12 months:

```bash
git-stats --bus-factor-months 12
```

---

## CLI Options

| Option | Description |
| :--- | :--- |
| `path` | Path to git repository (default: `.`) |
| `--since DATE` | Filter commits more recent than a specific date or interval (e.g. `1y`, `6m`, `2024-01-01`) |
| `--until DATE` | Filter commits older than a specific date or interval |
| `--branch REV`, `--rev REV` | Target branch, tag, or revision (e.g. `main`, `HEAD`) |
| `--all` | Include commits across all refs and branches |
| `--format {terminal,json,markdown,html}` | Primary output format (default: `terminal`) |
| `-o FILE`, `--output FILE` | Output file destination for primary format |
| `--html [FILE]` | Generate standalone HTML report |
| `--json [FILE]` | Output structured JSON data |
| `--markdown [FILE]`, `--md [FILE]` | Output GitHub Flavored Markdown |
| `--anonymize` | Pseudonymize contributor names and emails with SHA-256 |
| `--bus-factor-months N` | Evaluation window in months for bus factor calculation (default: `6`, `0` for all history) |
| `--top N` | Number of top authors, files, and languages to display (default: `10`) |
| `--tz {local,utc}` | Timezone for heatmap and commit activity metrics (default: `local`) |
| `--mailmap FILE` | Path to custom `.mailmap` file |
| `--version` | Display version number |
| `-h`, `--help` | Display help message |

---

## Architecture

```
git-stats-lite/
├── src/
│   └── git_stats_lite/
│       ├── __init__.py       # Package metadata
│       ├── cli.py            # Argument parsing and orchestration
│       ├── git.py            # Git subprocess execution and streaming output
│       ├── parser.py         # Log parser, rename resolution, mailmap
│       ├── models.py         # Data structures (dataclasses)
│       ├── stats.py          # Accumulator engine, bus factor calculation
│       ├── languages.py      # Extension and filename mapping
│       ├── anonymizer.py     # Deterministic SHA-256 identity hashing
│       └── formatters/
│           ├── terminal.py   # Text tables and ASCII heatmap
│           ├── json_fmt.py   # JSON serialization
│           ├── markdown.py   # GFM report renderer
│           └── html.py       # Self-contained HTML with inline SVG charts
└── tests/                    # Unit and integration test suite
```

---

## Running Tests

Run the test suite using Python's standard `unittest` runner:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Syntax verification:

```bash
python -m compileall src tests
```

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

Copyright (c) 2026 Yusuf Berat Zengin
