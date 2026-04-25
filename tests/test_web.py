"""Tests for Web UI backend."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from myagent.engine.messages import ConversationMessage
from myagent.engine.stream_events import (
    AssistantTurnComplete,
    PermissionRequestEvent,
    ToolExecutionCompleted,
    ToolExecutionStarted,
)
from myagent.web.engine_manager import WebEngineManager
from myagent.web.server import create_app
from myagent.web.session import SessionStore


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

    def test_update_system_prompt_persists_session(self, tmp_path: Path):
        """更新 system prompt 后应持久化到磁盘。"""
        app = create_app()

        with TestClient(app) as client:
            app.state.session_store = SessionStore(storage_dir=tmp_path)
            created = client.post("/api/sessions", json={"agent": "general"})
            session_id = created.json()["id"]

            response = client.patch(
                f"/api/sessions/{session_id}/system-prompt",
                json={"system_prompt": "你是新的系统提示"},
            )

        assert response.status_code == 200

        reloaded_store = SessionStore(storage_dir=tmp_path)
        reloaded = reloaded_store.get(session_id, user_id="default")
        assert reloaded is not None
        assert reloaded.system_prompt == "你是新的系统提示"
        assert reloaded.messages == []

    def test_import_messages_persists_session(self, tmp_path: Path):
        """导入消息后应持久化到磁盘。"""
        app = create_app()

        with TestClient(app) as client:
            app.state.session_store = SessionStore(storage_dir=tmp_path)
            created = client.post("/api/sessions", json={"agent": "general"})
            session_id = created.json()["id"]

            response = client.post(
                f"/api/sessions/{session_id}/import",
                json={
                    "messages": [
                        {"role": "user", "content": "你好"},
                        {"role": "assistant", "content": "你好，我在。"},
                    ],
                },
            )

        assert response.status_code == 200

        reloaded_store = SessionStore(storage_dir=tmp_path)
        reloaded = reloaded_store.get(session_id, user_id="default")
        assert reloaded is not None
        assert reloaded.messages == [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，我在。"},
        ]

    @pytest.mark.asyncio
    async def test_process_message_includes_tool_use_id_for_permission_events(self):
        """Web 事件序列化应完整透传 tool_use_id。"""
        manager = WebEngineManager()
        sent_events: list[dict[str, object]] = []

        async def send_callback(payload: dict[str, object]) -> None:
            sent_events.append(payload)

        class FakeEngine:
            async def submit_message(self, message: str):
                yield ToolExecutionStarted(
                    tool_name="bash",
                    tool_use_id="tool-123",
                    arguments={"command": "pwd"},
                )
                yield ToolExecutionCompleted(
                    tool_use_id="tool-123",
                    result="done",
                )
                yield PermissionRequestEvent(
                    tool_name="bash",
                    tool_use_id="tool-123",
                    arguments={"command": "rm -rf ."},
                    reason="需要危险命令审批",
                )
                yield AssistantTurnComplete(
                    message=ConversationMessage.from_assistant_text("ok"),
                )

        response = await manager.process_message(
            FakeEngine(),
            "hello",
            send_callback=send_callback,
        )

        assert response == ""
        assert sent_events == [
            {
                "type": "tool_call",
                "tool_name": "bash",
                "tool_use_id": "tool-123",
                "arguments": {"command": "pwd"},
            },
            {
                "type": "tool_result",
                "tool_use_id": "tool-123",
                "result": "done",
                "is_error": False,
            },
            {
                "type": "permission_request",
                "tool_name": "bash",
                "tool_use_id": "tool-123",
                "arguments": {"command": "rm -rf ."},
                "reason": "需要危险命令审批",
            },
        ]
