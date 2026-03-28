"""Tests for zer0dex seed — file collection and markdown chunking."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from zer0dex.seed import collect_files, chunk_markdown


class TestCollectFiles:
    def test_single_file(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("hello")
        result = collect_files([str(f)])
        assert len(result) == 1
        assert result[0] == f

    def test_directory_finds_md_files(self, tmp_path):
        (tmp_path / "a.md").write_text("a")
        (tmp_path / "b.md").write_text("b")
        (tmp_path / "c.txt").write_text("c")
        result = collect_files([str(tmp_path)])
        names = [r.name for r in result]
        assert "a.md" in names
        assert "b.md" in names
        assert "c.txt" not in names

    def test_nested_directory(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.md").write_text("nested")
        result = collect_files([str(tmp_path)])
        assert any(r.name == "nested.md" for r in result)

    def test_missing_path_returns_empty(self, tmp_path):
        result = collect_files([str(tmp_path / "nonexistent")])
        assert result == []

    def test_empty_directory(self, tmp_path):
        result = collect_files([str(tmp_path)])
        assert result == []

    def test_multiple_sources(self, tmp_path):
        f1 = tmp_path / "one.md"
        f2 = tmp_path / "two.md"
        f1.write_text("one")
        f2.write_text("two")
        result = collect_files([str(f1), str(f2)])
        assert len(result) == 2


class TestChunkMarkdown:
    def test_single_section(self):
        text = "# Title\nSome content here."
        chunks = chunk_markdown(text)
        assert len(chunks) == 1
        assert "Title" in chunks[0]

    def test_splits_on_h2(self):
        text = "# Title\nIntro\n## Section A\nContent A\n## Section B\nContent B"
        chunks = chunk_markdown(text)
        assert len(chunks) == 3  # title+intro, section A, section B

    def test_no_empty_chunks(self):
        text = "\n\n\n## A\nstuff\n\n\n## B\nmore\n\n"
        chunks = chunk_markdown(text)
        for c in chunks:
            assert c.strip() != ""

    def test_large_section_gets_split(self):
        big = "## Big\n" + ("word " * 1000)
        chunks = chunk_markdown(big, max_chunk=500)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c) <= 600  # some tolerance for word boundaries

    def test_empty_input(self):
        assert chunk_markdown("") == []

    def test_whitespace_only(self):
        assert chunk_markdown("   \n  \n  ") == []

    def test_preserves_content(self):
        text = "## Section\nImportant fact: zer0dex achieves 91% recall."
        chunks = chunk_markdown(text)
        joined = " ".join(chunks)
        assert "91% recall" in joined

    def test_h3_does_not_split(self):
        text = "## Main\nContent\n### Sub\nMore content"
        chunks = chunk_markdown(text)
        assert len(chunks) == 1  # h3 should not cause a split
