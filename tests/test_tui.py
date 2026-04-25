"""Tests for MyAgent TUI."""

from __future__ import annotations

from pathlib import Path

import pytest

from myagent.tui.app import MyAgentApp


@pytest.mark.asyncio
async def test_app_creation():
    app = MyAgentApp()
    assert app is not None
    assert isinstance(app, MyAgentApp)


@pytest.mark.asyncio
async def test_app_mount():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        assert pilot.app.is_mounted


@pytest.mark.asyncio
async def test_header_exists():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        header = pilot.app.query_one("#header")
        assert header is not None


@pytest.mark.asyncio
async def test_side_panel_exists():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        side_panel = pilot.app.query_one("#side-panel")
        assert side_panel is not None


@pytest.mark.asyncio
async def test_transcript_exists():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        transcript = pilot.app.query_one("#transcript")
        assert transcript is not None


@pytest.mark.asyncio
async def test_composer_exists():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        composer = pilot.app.query_one("#composer")
        assert composer is not None


@pytest.mark.asyncio
async def test_footer_exists():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        footer = pilot.app.query_one("#footer")
        assert footer is not None


@pytest.mark.asyncio
async def test_add_user_message():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        app.add_user_message("Hello")
        # RichLog stores lines internally, check via _lines or just verify no error
        transcript = pilot.app.query_one("#transcript")
        assert transcript is not None
        # Logo + welcome + user msg = 3 lines
        assert len(app._transcript_lines) == 3
        assert "Hello" in app._transcript_lines[-1]


@pytest.mark.asyncio
async def test_add_assistant_message():
    app = MyAgentApp()
    async with app.run_test():
        app.add_assistant_message("Hi there!")
        # Logo + welcome + assistant msg = 3 lines
        assert len(app._transcript_lines) == 3
        assert "Hi there!" in app._transcript_lines[-1]


@pytest.mark.asyncio
async def test_add_tool_call():
    app = MyAgentApp()
    async with app.run_test():
        app.add_tool_call("Read", {"path": "test.py"})
        # Logo + welcome + tool call = 3 lines
        assert len(app._transcript_lines) == 3
        assert "Read" in app._transcript_lines[-1]


@pytest.mark.asyncio
async def test_clear_transcript():
    app = MyAgentApp()
    async with app.run_test():
        app.add_user_message("Hello")
        app.clear_transcript()
        assert len(app._transcript_lines) == 0


@pytest.mark.asyncio
async def test_composer_input():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        composer = pilot.app.query_one("#composer")
        composer.value = "Test message"
        assert composer.value == "Test message"


@pytest.mark.asyncio
async def test_current_response_update():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        app.update_current_response("Thinking...")
        assert app._current_response_text == "Thinking..."
        response = pilot.app.query_one("#current-response")
        assert response is not None


@pytest.mark.asyncio
async def test_setup_required_message_for_incomplete_setup(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("MYAGENT_HOME", str(tmp_path))

    app = MyAgentApp()
    async with app.run_test():
        assert app.setup_status.overall_ready is False
        assert any("Setup Required" in line for line in app._transcript_lines)


@pytest.mark.asyncio
async def test_command_palette_action_opens_modal():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        app.action_command_palette()
        await pilot.pause()
        assert pilot.app.screen.__class__.__name__ == "CommandPaletteScreen"


@pytest.mark.asyncio
async def test_setup_command_opens_info_modal():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        app._handle_command("/setup")
        await pilot.pause()
        assert pilot.app.screen.__class__.__name__ == "InfoModalScreen"


@pytest.mark.asyncio
async def test_session_command_opens_info_modal():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        app._handle_command("/session")
        await pilot.pause()
        assert pilot.app.screen.__class__.__name__ == "InfoModalScreen"


@pytest.mark.asyncio
async def test_plan_command_updates_header_and_task_panel():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        app._handle_command("/plan 设计新的任务流")
        await pilot.pause()
        header = pilot.app.query_one("#header")
        task_panel = pilot.app.query_one("#task-panel")
        assert "Task: planning" in str(header.render())
        assert "State: planning" in str(task_panel.render())
        assert "设计新的任务流" in str(task_panel.render())


def test_plan_command_updates_task_state():
    app = MyAgentApp()
    app._handle_command("/plan 设计新的任务流")

    assert app.current_agent == "plan"
    assert app._task_status["state"] == "planning"
    assert app._task_status["request"] == "设计新的任务流"
