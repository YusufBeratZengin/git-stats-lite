# Contributing

Thank you for your interest in contributing to `git-stats-lite`!

Use Python 3.10 or newer and Git. From a source checkout:

```sh
# Install development dependencies in editable mode
python -m pip install -e ".[dev]"

# Run code style, typing, and test suite
python -m ruff check .
python -m mypy src examples
python -m pytest -q

# Run examples
python examples/demo.py
python examples/export_reports.py
python examples/analyze_repo.py

# Verify package build dry run
python -m build
python -m twine check dist/*
```

## Guidelines

- **Zero runtime dependencies**: Keep `dependencies = []` in `pyproject.toml`. The core tool relies exclusively on the Python standard library and local `git` CLI subprocess streaming.
- **Typed public API**: All functions and public dataclasses must include type annotations (`strict = true` in mypy).
- **Self-contained outputs**: Formatted reports (HTML, Markdown, JSON, terminal) must have no external font, CDN, or stylesheet dependencies.
- **Offline & synthetic tests**: All tests must run offline, complete within seconds, and use temporary synthetic git repositories or mocked data. Never include personal data or production credentials.
- **Documentation symmetry**: Always update `README.md` and `README.tr.md` together to keep English and Turkish documentation in sync.
- **Conventional Commits**: Format commit messages according to the Conventional Commits specification (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, `chore:`).
- **Code of Conduct**: Please adhere to the project's [Code of Conduct](CODE_OF_CONDUCT.md).

## Pull Requests

1. Create a focused topic branch.
2. Ensure `ruff`, `mypy`, and `pytest` are fully passing.
3. Update `CHANGELOG.md` under the `[Unreleased]` section.
4. Describe the problem, the solution, and verification steps in the pull request description.

## Releasing

Maintainers configure a PyPI trusted publisher for repository
`YusufBeratZengin/git-stats-lite`, workflow `publish.yml`, environment `pypi`.
Create that GitHub environment with appropriate release protections. No API token is required.

1. Move the relevant `[Unreleased]` entries into a dated SemVer release section.
2. Update the version in both `pyproject.toml` and `src/git_stats_lite/__init__.py`.
3. Run all checks above, including the build and `twine check` dry run.
4. Commit with `chore(release): vX.Y.Z`, then create tag `vX.Y.Z` and push it when approved.

The publish workflow verifies the tag against the package version, runs lint,
typing and tests, builds and checks distributions, then publishes using OIDC.
Stay on 0.x while the API is evolving; breaking changes increment the minor version.
