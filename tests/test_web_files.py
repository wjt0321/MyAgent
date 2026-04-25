"""Tests for Web UI file browser API."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from myagent.web.server import create_app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """在临时 cwd 中创建测试客户端。"""
    monkeypatch.chdir(tmp_path)
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

    def test_list_files_with_path(self, client):
        """应允许访问 cwd 范围内的指定路径。"""
        project_dir = Path.cwd() / "project"
        project_dir.mkdir()
        (project_dir / "test.txt").write_text("hello", encoding="utf-8")

        response = client.get(f"/api/files?path={project_dir}")
        assert response.status_code == 200
        data = response.json()
        names = [e["name"] for e in data["entries"]]
        assert "test.txt" in names

    def test_read_file(self, client):
        """应允许读取 cwd 范围内的文件内容。"""
        test_file = Path.cwd() / "test.txt"
        test_file.write_text("hello world", encoding="utf-8")

        response = client.get(f"/api/files/read?path={test_file}")
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "hello world"

    def test_reject_outside_workspace_path(self, client):
        """应拒绝访问 cwd 与 workspace 之外的路径。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            outside_dir = Path(tmpdir)
            (outside_dir / "secret.txt").write_text("nope", encoding="utf-8")

            list_response = client.get(f"/api/files?path={outside_dir}")
            read_response = client.get(
                f"/api/files/read?path={outside_dir / 'secret.txt'}"
            )

        assert list_response.status_code == 403
        assert read_response.status_code == 403
