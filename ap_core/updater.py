"""Self-update helpers for source and package installs."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: Path | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a command and return the completed process with captured output."""
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=check,
    )


def _print_process_failure(result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)


def _git_root(start: Path) -> Path | None:
    if not shutil.which("git"):
        return None

    git_cwd = start if start.is_dir() else start.parent
    result = _run(["git", "-C", str(git_cwd), "rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def _has_local_changes(repo: Path) -> bool:
    result = _run(["git", "-C", str(repo), "status", "--porcelain"])
    return bool(result.stdout.strip())


def _install_source_dependencies(repo: Path) -> bool:
    if shutil.which("uv"):
        print("Installing/updating dependencies with uv...")
        result = _run(["uv", "sync"], cwd=repo)
        if result.returncode != 0:
            _print_process_failure(result)
            return False

        print("Ensuring Playwright browser is installed...")
        result = _run(["uv", "run", "playwright", "install", "chromium"], cwd=repo)
        if result.returncode != 0:
            _print_process_failure(result)
            return False
        return True

    print("Installing/updating dependencies with pip...")
    result = _run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=repo)
    if result.returncode != 0:
        _print_process_failure(result)
        return False

    print("Ensuring Playwright browser is installed...")
    result = _run([sys.executable, "-m", "playwright", "install", "chromium"], cwd=repo)
    if result.returncode != 0:
        _print_process_failure(result)
        return False
    return True


def _update_from_git(repo: Path) -> int:
    print(f"Source checkout detected: {repo}")

    if _has_local_changes(repo):
        print("Update stopped because this checkout has uncommitted changes.")
        print("Commit or stash local edits, then run: autopahe --update")
        return 2

    branch = _run(["git", "-C", str(repo), "branch", "--show-current"])
    branch_name = branch.stdout.strip() or "current branch"
    print(f"Updating {branch_name}...")

    fetch = _run(["git", "-C", str(repo), "fetch", "--prune", "origin"])
    if fetch.returncode != 0:
        _print_process_failure(fetch)
        return fetch.returncode

    pull = _run(["git", "-C", str(repo), "pull", "--ff-only"])
    if pull.returncode != 0:
        _print_process_failure(pull)
        print("Fast-forward update failed. Resolve the branch state manually, then rerun autopahe --update.")
        return pull.returncode

    if pull.stdout.strip():
        print(pull.stdout.strip())

    if not _install_source_dependencies(repo):
        return 1

    print("AutoPahe is up to date.")
    return 0


def _update_from_package() -> int:
    if shutil.which("uv"):
        print("No source checkout found. Updating installed tool with uv...")
        result = _run(["uv", "tool", "upgrade", "autopahe"])
    elif sys.prefix == getattr(sys, "base_prefix", sys.prefix) and shutil.which("pipx"):
        print("No source checkout found. Updating installed package with pipx...")
        result = _run(["pipx", "upgrade", "autopahe"])
    else:
        print("No source checkout found. Updating installed package with pip...")
        result = _run([sys.executable, "-m", "pip", "install", "--upgrade", "autopahe"])

    if result.returncode != 0:
        _print_process_failure(result)
        print("If AutoPahe was installed with uv, run: uv tool upgrade autopahe")
        print("If AutoPahe was installed with pipx, run: pipx upgrade autopahe")
        print("If it was installed with pip, run it from the same virtual environment and retry: autopahe --update")
        return result.returncode

    if result.stdout.strip():
        print(result.stdout.strip())

    print("Ensuring Playwright browser is installed...")
    browser = _run([sys.executable, "-m", "playwright", "install", "chromium"])
    if browser.returncode != 0:
        _print_process_failure(browser)
        return browser.returncode

    print("AutoPahe is up to date.")
    return 0


def self_update(start: Path | None = None) -> int:
    """Update AutoPahe from git when possible, otherwise upgrade the package."""
    start_path = (start or Path(__file__).resolve()).resolve()
    repo = _git_root(start_path)
    if repo is not None:
        return _update_from_git(repo)
    return _update_from_package()
