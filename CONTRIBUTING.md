# Contributing to git-stats-lite

Thank you for your interest in contributing to `git-stats-lite`.

## Core Guidelines

- **Zero Runtime Dependencies:** The core package must rely exclusively on the Python standard library and system `git`. Do not add third-party runtime dependencies.
- **Privacy First:** Ensure author information and file metadata are handled responsibly. Any new features exposing contributor details must integrate with the `--anonymize` pipeline.
- **Python Compatibility:** Python >=3.10 is required. Ensure code complies with modern typing and standard library features.
- **Conventional Commits:** Use standard Conventional Commits format (e.g. `feat: add metric`, `fix: handle binary diffs`, `test: add unit test`).

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/YusufBeratZengin/git-stats-lite.git
   cd git-stats-lite
   ```

2. Verify that Python 3.10 or newer and Git are installed:
   ```bash
   python --version
   git --version
   ```

3. Run the test suite:
   ```bash
   python -m unittest discover -s tests -p "test_*.py" -v
   ```

4. Verify syntax:
   ```bash
   python -m compileall src tests
   ```

## Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/my-feature
   ```
2. Write clean code and accompanying unit tests.
3. Ensure all tests pass with zero failures before opening a pull request.
4. Open a pull request against `main` on GitHub:
   https://github.com/YusufBeratZengin/git-stats-lite/pulls

## Code Style

- Keep functions focused and well-documented.
- Avoid external CSS/JS libraries in the HTML report generator. All inline SVG and CSS styles must remain self-contained.
- Use explicit type annotations for public APIs and data models.
