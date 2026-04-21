"""Tests for health check endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from myagent.web.health import router


@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestHealthEndpoints:
    def test_liveness(self, client):
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"

    def test_readiness(self, client):
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert "ready" in response.text

    def test_health_check(self, client):
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
        assert "version" in data

    def test_metrics(self, client):
        response = client.get("/health/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
