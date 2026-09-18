"""Lightweight check that machine-readable docs agree with pyproject.toml on version."""
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _pyproject_version() -> str:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    return data["project"]["version"]


def test_llms_txt_version_matches_pyproject():
    pyproject_version = _pyproject_version()
    llms_text = (REPO_ROOT / "llms.txt").read_text()
    match = re.search(r"Version (\d+\.\d+\.\d+) is the first", llms_text)
    assert match, "llms.txt is missing the expected 'Version X.Y.Z is the first' line"
    assert match.group(1) == pyproject_version, (
        f"llms.txt declares version {match.group(1)!r} but pyproject.toml "
        f"declares {pyproject_version!r}"
    )


def test_codemeta_version_matches_pyproject():
    import json

    pyproject_version = _pyproject_version()
    codemeta = json.loads((REPO_ROOT / "codemeta.json").read_text())
    assert codemeta["version"] == pyproject_version
