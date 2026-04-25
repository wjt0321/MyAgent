"""Tests for Web UI backend."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from myagent.web.server import create_app


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    with TestClient(app) as c:
        yield c


class TestWebServer:
    def test_root_redirects_to_index(self, client):
        """Root path should serve the index page."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        html = response.text
        assert 'id="workbench-nav"' in html
        assert 'id="detail-sidebar"' in html
        assert 'id="command-palette-modal"' in html
        assert 'data-view="chat"' in html
        assert 'id="session-status-chip"' in html
        assert 'id="welcome-recent-sessions"' in html

    def test_health_endpoint(self, client):
        """Health check endpoint should return ok."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_list_sessions(self, client):
        """Should list sessions."""
        response = client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_session(self, client):
        """Should create a new session."""
        response = client.post("/api/sessions", json={"agent": "general"})
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["agent"] == "general"

    def test_static_app_contains_workbench_behaviors(self, client):
        """Static app bundle should include workbench interaction hooks."""
        response = client.get("/static/app.js")
        assert response.status_code == 200
        content = response.text
        assert "setActiveView(" in content
        assert "showCommandPalette(" in content
        assert "executeSlashCommand(" in content
        assert "renderDetailSidebar(" in content
