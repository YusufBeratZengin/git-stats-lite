# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Typed package marker, development dependencies, cross-platform quality checks, and tag-triggered PyPI trusted publishing workflow.
- Community templates and a runnable offline demo with matching English and Turkish documentation.
- Regression coverage for relative date filters, timezone boundaries, and bus factor windows.

### Fixed

- Ruff findings and Markdown formatter type errors without changing report formatting.
- Relative date shorthand such as `--since 1y` and `--until 6m` now uses Git's supported relative date syntax.
- First and last commit dates are now displayed in the HTML report header.

## [0.1.0] - 2026-10-22

### Added

- Streaming git log parser using `git log --numstat --format=...` via subprocess with zero external runtime dependencies.
- Author metrics aggregation with `.mailmap` support and email normalization (resolves GitHub and GitLab noreply aliases).
- Weekday-hour 7x24 commit activity heatmap supporting both local author timezone and UTC.
- Commits per day and per week historical trends.
- File churn and hotspot score calculations (`changes * size`).
- Programming language breakdown based on file extension and special filenames.
- Bus factor risk assessment calculating the minimum contributors covering 50% and 80% of lines changed within a configurable month window.
- Multiple report formats: formatted terminal tables, structured JSON, GitHub Flavored Markdown, and standalone single-file HTML.
- Self-contained HTML report with responsive inline SVG charts (heatmap, commit timeline, top authors, language distribution) and light/dark theme support.
- Privacy mode (`--anonymize`) providing deterministic SHA-256 pseudonymization of author names and email addresses.
- Command-line interface with options `--since`, `--until`, `--branch`, `--all`, `--html`, `--json`, `--markdown`, `--format`, `--output`, `--anonymize`, `--bus-factor-months`, `--top`, and `--tz`.
- Comprehensive test suite covering units and end-to-end scripted git repository workflows.
