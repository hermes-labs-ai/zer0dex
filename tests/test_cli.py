"""Tests for zer0dex CLI — config, parsing, and check command."""
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from zer0dex.cli import load_config, save_config, main


@pytest.fixture
def tmp_workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestConfig:
    def test_load_config_missing_file(self, tmp_workdir):
        assert load_config() == {}

    def test_save_and_load_roundtrip(self, tmp_workdir):
        cfg = {"collection": "test", "port": 9999}
        save_config(cfg)
        loaded = load_config()
        assert loaded == cfg

    def test_save_creates_json_file(self, tmp_workdir):
        save_config({"key": "val"})
        raw = (tmp_workdir / ".zer0dex.json").read_text()
        assert json.loads(raw) == {"key": "val"}


class TestCLIParsing:
    def test_help_exits_zero(self):
        result = subprocess.run(
            [sys.executable, "-m", "zer0dex.cli", "--help"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
            env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent / "src")},
        )
        assert result.returncode == 0
        assert "zer0dex" in result.stdout

    def test_no_command_exits_nonzero(self):
        result = subprocess.run(
            [sys.executable, "-m", "zer0dex.cli"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
            env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent / "src")},
        )
        assert result.returncode == 1

    def test_check_subcommand_in_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "zer0dex.cli", "--help"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
            env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent / "src")},
        )
        assert "check" in result.stdout

    def test_all_commands_in_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "zer0dex.cli", "--help"],
            capture_output=True, text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
            env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent / "src")},
        )
        for cmd in ["check", "init", "seed", "serve", "query", "status", "add"]:
            assert cmd in result.stdout, f"Missing command: {cmd}"


class TestInit:
    def test_init_creates_config_and_dir(self, tmp_workdir):
        result = subprocess.run(
            [sys.executable, "-m", "zer0dex.cli", "init"],
            capture_output=True, text=True,
            cwd=str(tmp_workdir),
            env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent / "src")},
        )
        assert result.returncode == 0
        assert (tmp_workdir / ".zer0dex.json").exists()
        assert (tmp_workdir / ".zer0dex").is_dir()

    def test_init_config_has_required_keys(self, tmp_workdir):
        subprocess.run(
            [sys.executable, "-m", "zer0dex.cli", "init"],
            capture_output=True, text=True,
            cwd=str(tmp_workdir),
            env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent / "src")},
        )
        cfg = json.loads((tmp_workdir / ".zer0dex.json").read_text())
        for key in ["collection", "chroma_path", "port", "user_id", "llm_model", "embed_model", "ollama_url"]:
            assert key in cfg, f"Missing config key: {key}"

    def test_init_custom_collection(self, tmp_workdir):
        subprocess.run(
            [sys.executable, "-m", "zer0dex.cli", "init", "--collection", "mytest"],
            capture_output=True, text=True,
            cwd=str(tmp_workdir),
            env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent / "src")},
        )
        cfg = json.loads((tmp_workdir / ".zer0dex.json").read_text())
        assert cfg["collection"] == "mytest"


class TestCheck:
    def test_check_fails_without_ollama(self, tmp_workdir):
        """check should exit 1 when Ollama isn't running."""
        save_config({"ollama_url": "http://localhost:99999"})
        result = subprocess.run(
            [sys.executable, "-m", "zer0dex.cli", "check"],
            capture_output=True, text=True,
            cwd=str(tmp_workdir),
            env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).resolve().parent.parent / "src")},
        )
        assert result.returncode == 1
        assert "not reachable" in result.stdout or "not reachable" in result.stderr
