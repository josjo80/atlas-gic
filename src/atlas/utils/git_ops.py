"""Git operations for the autoresearch loop.

All functions that perform real git work use subprocess.run.
They raise RuntimeError on failure so the caller can fall back gracefully.
"""
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def _git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result


def get_repo_root() -> Path:
    result = _git(["rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip())


def get_current_branch(repo: Path) -> str:
    return _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo).stdout.strip()


def create_branch(name: str, repo: Path) -> None:
    _git(["checkout", "-b", name], cwd=repo)


def checkout_branch(name: str, repo: Path) -> None:
    _git(["checkout", name], cwd=repo)


def delete_branch(name: str, repo: Path) -> None:
    _git(["branch", "-D", name], cwd=repo)


def commit_file(file_path: Path, message: str, repo: Path) -> None:
    """Stage a single file and create a commit."""
    _git(["add", str(file_path)], cwd=repo)
    _git(["commit", "-m", message], cwd=repo)


# ── Legacy mock stubs (kept for tests that import them directly) ──────────────

def mock_commit(message: str) -> None:
    logger.debug("[git mock] commit: %s", message)
    print(f"[git] commit: {message}")


def mock_revert() -> None:
    logger.debug("[git mock] revert")
    print("[git] revert")
