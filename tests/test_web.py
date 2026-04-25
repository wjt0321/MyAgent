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
from myagent.tasks.models import SubTask, Task, TaskStatus
from myagent.tasks.models import TaskResult
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

    def test_setup_status_endpoint_reports_missing_setup(self, monkeypatch, tmp_path: Path):
        """未初始化时应返回 setup status。"""
        monkeypatch.setenv("MYAGENT_HOME", str(tmp_path))
        app = create_app()

        with TestClient(app) as client:
            response = client.get("/api/setup/status")

        assert response.status_code == 200
        data = response.json()
        assert data["overall_ready"] is False
        assert data["workspace_ready"] is False
        assert data["llm_ready"] is False
        assert data["next_action"] == "myagent init --quick"

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

    def test_static_app_contains_workbench_behaviors(self, client):
        """Static app bundle should include workbench interaction hooks."""
        response = client.get("/static/app.js")
        assert response.status_code == 200
        content = response.text
        assert "setActiveView(" in content
        assert "showCommandPalette(" in content
        assert "executeSlashCommand(" in content
        assert "renderDetailSidebar(" in content
        assert "startTaskPolling(" in content
        assert "cancelTask(" in content
        assert "retryTask(" in content
        assert "restoreTask(" in content
        assert "task-team-summary" in content
        assert "task-review-card" in content
        assert "renderTaskTimeline(" in content
        assert "task-timeline-list" in content
        assert "task-review-deliverables" in content
        assert "task-review-issues" in content
        assert "task-review-suggestions" in content
        assert "result.summary" in content
        assert "<<<<<<<" not in content

    def test_static_shell_exposes_phase5_brand_tokens(self, client):
        """Phase 5 首批应统一品牌命名与主题 token。"""
        html_response = client.get("/")
        css_response = client.get("/static/style.css")
        assert html_response.status_code == 200
        assert css_response.status_code == 200
        html = html_response.text
        css = css_response.text
        assert "<title>MyAgent Workbench</title>" in html
        assert "MyAgent Workbench" in html
        assert "--brand-primary" in css
        assert "--brand-gradient" in css
        assert "--panel-glow" in css

    def test_static_app_contains_phase5_welcome_and_empty_states(self, client):
        """Phase 5 第二批应重做欢迎页与任务空状态。"""
        js_response = client.get("/static/app.js")
        css_response = client.get("/static/style.css")
        assert js_response.status_code == 200
        assert css_response.status_code == 200
        js = js_response.text
        css = css_response.text
        assert "welcome-hero" in js
        assert "welcome-action-card" in js
        assert "welcome-help-list" in js
        assert "task-empty-title" in js
        assert "task-empty-desc" in js
        assert "task-empty-actions" in js
        assert ".welcome-hero" in css
        assert ".welcome-action-card" in css
        assert ".task-empty-actions" in css

    def test_static_app_contains_phase5_tool_event_cards(self, client):
        """Phase 5 第三批应提供统一的新版工具卡片系统。"""
        js_response = client.get("/static/app.js")
        css_response = client.get("/static/style.css")
        assert js_response.status_code == 200
        assert css_response.status_code == 200
        js = js_response.text
        css = css_response.text
        assert "renderToolEventCard(" in js
        assert "summarizeToolResult(" in js
        assert "tool-status-chip" in js
        assert "tool-event-summary" in js
        assert "this.toolCallRegistry" in js
        assert ".tool-event-card-v2" in css
        assert ".tool-status-chip" in css
        assert ".tool-event-summary" in css
        assert ".tool-event-meta" in css

    def test_static_shell_contains_phase5_mobile_workbench_hooks(self, client):
        """Phase 5 第四批应补窄屏工作台可用性钩子。"""
        html_response = client.get("/")
        js_response = client.get("/static/app.js")
        css_response = client.get("/static/style.css")
        assert html_response.status_code == 200
        assert js_response.status_code == 200
        assert css_response.status_code == 200
        html = html_response.text
        js = js_response.text
        css = css_response.text
        assert 'id="mobile-view-chip"' in html
        assert "syncResponsiveWorkbenchState(" in js
        assert "updateMobileViewChip(" in js
        assert "scrollActiveWorkbenchNavIntoView(" in js
        assert ".mobile-view-chip" in css
        assert ".detail-sidebar.show-mobile" in css
        assert ".workbench-nav-scroll" in css

    def test_current_task_endpoint_returns_task_snapshot_and_team(self):
        """当前任务接口应返回任务快照与团队概览。"""
        app = create_app()
        task = Task(
            title="实现 Phase 4",
            description="让任务流对用户可见",
            status=TaskStatus.EXECUTING,
            subtasks=[SubTask(description="接入任务快照", status=TaskStatus.EXECUTING)],
        )
        task.events = [
            {
                "type": "member_assigned",
                "message": "Planner 已接手任务",
                "timestamp": "2026-04-25T12:00:00",
            }
        ]

        with TestClient(app) as client:
            app.state.task_engine._current_task = task
            response = client.get("/api/tasks/current")

        assert response.status_code == 200
        data = response.json()
        assert data["task"]["id"] == task.id
        assert data["task"]["status"] == "executing"
        assert data["task"]["events"][0]["type"] == "member_assigned"
        assert "Planner" in data["task"]["events"][0]["message"]
        assert data["team"]["total_members"] >= 1
        assert data["restore_available"] is True

    def test_cancel_task_endpoint_marks_current_task_cancelled(self):
        """取消任务接口应将当前任务标记为 cancelled。"""
        app = create_app()
        task = Task(
            title="实现 Phase 4",
            description="让任务流对用户可见",
            status=TaskStatus.EXECUTING,
            subtasks=[SubTask(description="接入任务快照", status=TaskStatus.EXECUTING)],
        )

        with TestClient(app) as client:
            app.state.task_engine._current_task = task
            response = client.post(f"/api/tasks/{task.id}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["task"]["status"] == "cancelled"

    def test_retry_task_endpoint_resets_failed_task(self):
        """重试接口应重置失败任务并重新进入待执行状态。"""
        app = create_app()
        task = Task(
            title="实现 Phase 4",
            description="让任务流对用户可见",
            status=TaskStatus.FAILED,
            subtasks=[
                SubTask(
                    description="失败的子任务",
                    status=TaskStatus.FAILED,
                    error="boom",
                    result="old result",
                )
            ],
        )
        task.result = TaskResult(summary="old review")

        with TestClient(app) as client:
            app.state.task_engine._current_task = task
            response = client.post(f"/api/tasks/{task.id}/retry")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "retried"
        assert data["task"]["status"] == "planned"
        assert data["task"]["subtasks"][0]["status"] == "pending"
        assert data["task"]["subtasks"][0]["error"] is None

    def test_retry_task_endpoint_rejects_non_retryable_status(self):
        """只有 failed 或 cancelled 的任务才能重试。"""
        app = create_app()
        task = Task(
            title="实现 Phase 4",
            description="让任务流对用户可见",
            status=TaskStatus.EXECUTING,
            subtasks=[SubTask(description="执行中的子任务", status=TaskStatus.EXECUTING)],
        )

        with TestClient(app) as client:
            app.state.task_engine._current_task = task
            response = client.post(f"/api/tasks/{task.id}/retry")

        assert response.status_code == 400

    def test_restore_task_endpoint_recovers_last_snapshot(self):
        """恢复接口应把最近任务快照重新挂回当前任务。"""
        app = create_app()
        task = Task(
            title="恢复任务快照",
            description="验证 restore 流程",
            status=TaskStatus.CANCELLED,
            subtasks=[SubTask(description="恢复子任务", status=TaskStatus.CANCELLED)],
        )

        with TestClient(app) as client:
            app.state.task_engine._current_task = None
            app.state.task_engine._last_task_snapshot = task
            response = client.post("/api/tasks/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "restored"
        assert data["task"]["title"] == "恢复任务快照"
        assert data["task"]["status"] == "cancelled"
