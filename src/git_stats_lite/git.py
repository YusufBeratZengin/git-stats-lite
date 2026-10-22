"""Git subprocess wrappers and streaming utilities."""

from __future__ import annotations

import os
import subprocess
from typing import Generator, List, Optional


class GitError(Exception):
    """Raised when a git command fails unexpectedly."""


def is_git_available() -> bool:
    """Check if git executable is available in PATH."""
    try:
        res = subprocess.run(
            ["git", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return res.returncode == 0
    except (FileNotFoundError, OSError):
        return False


def is_git_repository(path: str = ".") -> bool:
    """Check if the specified path is inside a working git repository."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return res.returncode == 0 and res.stdout.strip() == "true"
    except (FileNotFoundError, OSError):
        return False


def get_repo_root(path: str = ".") -> str:
    """Retrieve absolute root path of the git repository."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return os.path.abspath(res.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise GitError(f"Failed to find repository root for '{path}': {e.stderr.strip()}") from e


def get_current_branch(repo_path: str = ".") -> str:
    """Retrieve the current active branch name or revision."""
    try:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        branch = res.stdout.strip()
        if branch:
            return branch
        # Detached HEAD or fallback
        res2 = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        rev = res2.stdout.strip()
        return rev if rev else "HEAD"
    except Exception:
        return "HEAD"


def stream_git_log(
    repo_path: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
    revision: Optional[str] = None,
    all_branches: bool = False,
) -> Generator[str, None, None]:
    """Execute git log with streaming stdout.

    Yields raw output lines from `git log --numstat --use-mailmap ...`.
    """
    format_spec = "@@@COMMIT@@@%x00%H%x00%aN%x00%aE%x00%aI%x00%at%x00%cI%x00%ct%x00%s"
    cmd: List[str] = [
        "git",
        "log",
        "--use-mailmap",
        "--numstat",
        f"--format={format_spec}",
    ]

    if all_branches:
        cmd.append("--all")
    if since:
        cmd.append(f"--since={since}")
    if until:
        cmd.append(f"--until={until}")
    if revision:
        cmd.append(revision)

    proc = subprocess.Popen(
        cmd,
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    try:
        if proc.stdout:
            for line in proc.stdout:
                yield line
    finally:
        if proc.stdout:
            try:
                proc.stdout.close()
            except Exception:
                pass

    stderr_output = ""
    if proc.stderr:
        try:
            stderr_output = proc.stderr.read()
            proc.stderr.close()
        except Exception:
            pass
    proc.wait()

    if proc.returncode != 0:
        lower_err = stderr_output.lower()
        # Allow empty repository without error
        if "does not have any commits yet" in lower_err or "bad default revision 'head'" in lower_err:
            return
        raise GitError(f"git log failed (code {proc.returncode}): {stderr_output.strip()}")
