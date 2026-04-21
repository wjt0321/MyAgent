"""Tests for TextToSpeech tool."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from myagent.tools.base import ToolExecutionContext, ToolResult
from myagent.tools.text_to_speech import TextToSpeech, TextToSpeechInput


class TestTextToSpeechInput:
    def test_input_creation(self):
        inp = TextToSpeechInput(text="Hello world", output_path="/tmp/hello.mp3")
        assert inp.text == "Hello world"
        assert inp.output_path == "/tmp/hello.mp3"
        assert inp.voice == "default"

    def test_input_with_voice(self):
        inp = TextToSpeechInput(text="Hi", output_path="out.mp3", voice="female")
        assert inp.voice == "female"


class TestTextToSpeechTool:
    def test_tool_creation(self):
        tool = TextToSpeech()
        assert tool.name == "TextToSpeech"
        assert "speech" in tool.description.lower() or "audio" in tool.description.lower()

    def test_tool_is_read_only(self):
        tool = TextToSpeech()
        assert tool.is_read_only(None) is False

    @pytest.mark.asyncio
    async def test_synthesize_success(self, tmp_path: Path):
        tool = TextToSpeech()
        ctx = ToolExecutionContext(cwd=tmp_path)

        output_file = tmp_path / "output.mp3"

        mock_provider = MagicMock()
        mock_provider.synthesize.return_value = b"fake audio data"

        with patch.object(tool, "_get_provider", return_value=mock_provider):
            result = await tool.execute(
                TextToSpeechInput(text="Hello", output_path=str(output_file)),
                ctx,
            )

        assert result.is_error is False
        assert output_file.exists()
        assert output_file.read_bytes() == b"fake audio data"

    @pytest.mark.asyncio
    async def test_synthesize_empty_text(self, tmp_path: Path):
        tool = TextToSpeech()
        ctx = ToolExecutionContext(cwd=tmp_path)

        result = await tool.execute(
            TextToSpeechInput(text="", output_path="out.mp3"),
            ctx,
        )

        assert result.is_error is True
        assert "empty" in result.output.lower()

    @pytest.mark.asyncio
    async def test_synthesize_no_provider(self, tmp_path: Path):
        tool = TextToSpeech()
        ctx = ToolExecutionContext(cwd=tmp_path)

        with patch.object(tool, "_get_provider", return_value=None):
            result = await tool.execute(
                TextToSpeechInput(text="Hello", output_path="out.mp3"),
                ctx,
            )

        assert result.is_error is True
        assert "no tts provider" in result.output.lower()

    @pytest.mark.asyncio
    async def test_synthesize_provider_error(self, tmp_path: Path):
        tool = TextToSpeech()
        ctx = ToolExecutionContext(cwd=tmp_path)

        mock_provider = MagicMock()
        mock_provider.synthesize.side_effect = Exception("TTS failed")

        with patch.object(tool, "_get_provider", return_value=mock_provider):
            result = await tool.execute(
                TextToSpeechInput(text="Hello", output_path="out.mp3"),
                ctx,
            )

        assert result.is_error is True
        assert "tts failed" in result.output.lower()

    @pytest.mark.asyncio
    async def test_synthesize_auto_filename(self, tmp_path: Path):
        tool = TextToSpeech()
        ctx = ToolExecutionContext(cwd=tmp_path)

        mock_provider = MagicMock()
        mock_provider.synthesize.return_value = b"audio"

        with patch.object(tool, "_get_provider", return_value=mock_provider):
            result = await tool.execute(
                TextToSpeechInput(text="Hello world"),
                ctx,
            )

        assert result.is_error is False
        assert ".mp3" in result.output
