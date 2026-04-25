"""Tests for Web UI file browser API."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from myagent.web.server import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


class TestWebFileBrowser:
    def test_list_files_root(self, client):
        """Should list files in current directory."""
        response = client.get("/api/files")
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert isinstance(data["entries"], list)

    def test_list_files_with_path(self, client, monkeypatch):
        """Should list files in specified path."""
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "test.txt").write_text("hello")
            monkeypatch.chdir(tmpdir)
            response = client.get(f"/api/files?path={tmpdir}")
            assert response.status_code == 200
            data = response.json()
            names = [e["name"] for e in data["entries"]]
            assert "test.txt" in names
            monkeypatch.chdir(original_cwd)

    def test_read_file(self, client, monkeypatch):
        """Should read file content."""
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "test.txt")
            test_file.write_text("hello world")
            monkeypatch.chdir(tmpdir)
            response = client.get(f"/api/files/read?path={test_file}")
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "hello world"
            monkeypatch.chdir(original_cwd)
