"""Lightweight checks that machine-readable docs agree with pyproject.toml."""
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _pyproject_version() -> str:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    return data["project"]["version"]


def _pyproject_license() -> str:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    return data["project"]["license"]


def test_llms_txt_version_matches_pyproject():
    pyproject_version = _pyproject_version()
    llms_text = (REPO_ROOT / "llms.txt").read_text()
    match = re.search(r"Version (\d+\.\d+\.\d+) continues", llms_text)
    assert match, "llms.txt is missing the expected 'Version X.Y.Z continues' line"
    assert match.group(1) == pyproject_version, (
        f"llms.txt declares version {match.group(1)!r} but pyproject.toml "
        f"declares {pyproject_version!r}"
    )


def test_codemeta_version_matches_pyproject():
    import json

    pyproject_version = _pyproject_version()
    codemeta = json.loads((REPO_ROOT / "codemeta.json").read_text())
    assert codemeta["version"] == pyproject_version


def test_runtime_and_citation_versions_match_pyproject():
    pyproject_version = _pyproject_version()
    init_text = (REPO_ROOT / "src" / "zer0dex" / "__init__.py").read_text()
    citation_text = (REPO_ROOT / "CITATION.cff").read_text()

    assert re.search(rf'^__version__ = "{re.escape(pyproject_version)}"$', init_text, re.M)
    assert re.search(rf'^version: "{re.escape(pyproject_version)}"$', citation_text, re.M)


def test_project_license_metadata_matches_pyproject():
    import json

    license_id = _pyproject_license()
    assert license_id == "Apache-2.0"

    skill_text = (REPO_ROOT / ".agents" / "skills" / "zer0dex" / "SKILL.md").read_text()
    citation_text = (REPO_ROOT / "CITATION.cff").read_text()
    readme_text = (REPO_ROOT / "README.md").read_text()
    codemeta = json.loads((REPO_ROOT / "codemeta.json").read_text())

    assert re.search(r"^license: (\S+)$", skill_text, re.M).group(1) == license_id
    assert re.search(r"^license: (\S+)$", citation_text, re.M).group(1) == license_id
    assert codemeta["license"] == f"https://spdx.org/licenses/{license_id}"
    assert re.search(rf"^{re.escape(license_id)}\.", readme_text, re.M)
