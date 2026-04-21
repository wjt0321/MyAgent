"""Tests for MyAgent TUI."""

import pytest
from textual.pilot import Pilot

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
        assert len(app._transcript_lines) == 2  # welcome + user msg
        assert "Hello" in app._transcript_lines[-1]


@pytest.mark.asyncio
async def test_add_assistant_message():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        app.add_assistant_message("Hi there!")
        assert len(app._transcript_lines) == 2  # welcome + assistant msg
        assert "Hi there!" in app._transcript_lines[-1]


@pytest.mark.asyncio
async def test_add_tool_call():
    app = MyAgentApp()
    async with app.run_test() as pilot:
        app.add_tool_call("Read", {"path": "test.py"})
        assert len(app._transcript_lines) == 2  # welcome + tool call
        assert "Read" in app._transcript_lines[-1]


@pytest.mark.asyncio
async def test_clear_transcript():
    app = MyAgentApp()
    async with app.run_test() as pilot:
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
