from pathlib import Path

from ap_core.updater import _git_root


def test_git_root_accepts_file_path_inside_repo():
    root = _git_root(Path(__file__).resolve())

    assert root is not None
    assert (root / "pyproject.toml").exists()
