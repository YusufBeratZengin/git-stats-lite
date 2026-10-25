# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Runnable programmatic examples: `examples/export_reports.py` demonstrating multi-format reporting and `examples/analyze_repo.py` demonstrating local repository analysis via Python API.
- GitHub documentation issue template (`.github/ISSUE_TEMPLATE/documentation.yml`).
- Extended unit test suite covering bus factor fallback windows, empty reports, mailmap parsing edge cases, formatter empty states, and direct script execution.

### Changed

- Expanded README (English and Turkish) with `--format`, `-o`, `--mailmap` CLI options, Python API report formatting snippets, and a dedicated examples index.
- Updated `CONTRIBUTING.md` with guidelines on zero dependencies, offline synthetic tests, typed public APIs, and example verification.

### Fixed

- Reject invalid `--since` and `--until` dates before invoking Git.
- Reject negative `--bus-factor-months` and non-positive `--top` values while preserving `--bus-factor-months 0` for all history.
- Show a concise error for unknown branches or revisions.
- Add matching README headings and clarify that installation is local until the package is published on PyPI.

## [0.1.0] - 2026-10-23

### Added

- Streaming git log parser using `git log --numstat --format=...` via subprocess with zero external runtime dependencies.
- Author metrics aggregation with `.mailmap` support and email normalization (resolves GitHub and GitLab noreply aliases).
- Weekday-hour 7x24 commit activity heatmap supporting both local author timezone and UTC.
- Commits per day and per week historical trends.
- File churn and hotspot score calculations (`changes * size`).
- Programming language breakdown based on file extension and special filenames.
- Bus factor risk assessment calculating the minimum contributors covering 50% and 80% of lines changed within a configurable month window.
- Multiple report formats: formatted terminal tables, structured JSON, GitHub Flavored Markdown, and standalone single-file HTML.
- Self-contained HTML report with responsive inline SVG charts (heatmap, commit timeline, top authors, language distribution) and automatic light/dark theme support.
- Privacy mode (`--anonymize`) providing deterministic SHA-256 pseudonymization of author names and email addresses.
- Command-line interface with options `--since`, `--until`, `--branch`, `--all`, `--html`, `--json`, `--markdown`, `--format`, `--output`, `--anonymize`, `--bus-factor-months`, `--top`, and `--tz`.
- Comprehensive test suite with over 95% line coverage covering units and end-to-end scripted git repository workflows.
- Cross-platform CI matrix covering Linux, Windows, and macOS across Python 3.10 and 3.12 with automated CodeQL static analysis.
- Terminal demo generator (`scripts/make-demo.py`) producing high-resolution dark-mode SVG previews (`docs/demo.svg`).
