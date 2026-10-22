# Contributing

Use Python 3.10 or newer and Git. From a source checkout:

```sh
python -m pip install -e ".[dev]"
python -m ruff check .
python -m mypy src
python -m pytest -q
python examples/demo.py
python -m build
python -m twine check dist/*
```

Keep runtime dependencies empty, public APIs typed, and reports self-contained.
Tests must run offline and use synthetic identities and temporary repositories.
Keep README.md and README.tr.md in sync. Follow [the code of conduct](CODE_OF_CONDUCT.md).
Use Conventional Commits (`feat:`, `fix:`, `docs:`, `ci:`, `chore:`, `test:`).
Describe the resulting behavior and validation in each pull request.

## Releasing

Maintainers configure a PyPI trusted publisher for repository
`YusufBeratZengin/git-stats-lite`, workflow `publish.yml`, environment `pypi`.
Create that GitHub environment with appropriate release protections. No API token is required.

1. Move the relevant `[Unreleased]` entries into a dated SemVer release section.
2. Update the version in both pyproject.toml and src/git_stats_lite/__init__.py.
3. Run all checks above, including the build and `twine check` dry run.
4. Commit with `chore(release): vX.Y.Z`, then create tag `vX.Y.Z` and push it when approved.

The publish workflow verifies the tag against the package version, runs lint,
typing and tests, builds and checks distributions, then publishes using OIDC.
Stay on 0.x while the API is evolving; breaking changes increment the minor version.
