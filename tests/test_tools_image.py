"""Tests for ImageAnalyze tool."""

import base64
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from myagent.tools.base import ToolExecutionContext, ToolResult
from myagent.tools.image_analyze import ImageAnalyze, ImageAnalyzeInput


class TestImageAnalyzeInput:
    def test_input_creation(self):
        inp = ImageAnalyzeInput(
            image_path="/tmp/test.png",
            prompt="Describe this image",
        )
        assert inp.image_path == "/tmp/test.png"
        assert inp.prompt == "Describe this image"

    def test_input_with_url(self):
        inp = ImageAnalyzeInput(
            image_url="https://example.com/image.jpg",
            prompt="What is this?",
        )
        assert inp.image_url == "https://example.com/image.jpg"
        assert inp.prompt == "What is this?"


class TestImageAnalyzeTool:
    def test_tool_creation(self):
        tool = ImageAnalyze()
        assert tool.name == "ImageAnalyze"
        assert "image" in tool.description.lower()

    def test_tool_is_read_only(self):
        tool = ImageAnalyze()
        assert tool.is_read_only(None) is True

    @pytest.mark.asyncio
    async def test_analyze_local_image(self, tmp_path: Path):
        tool = ImageAnalyze()
        ctx = ToolExecutionContext(cwd=tmp_path)

        image_file = tmp_path / "test.png"
        image_file.write_bytes(b"fake png data")

        mock_provider = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.text = "This is a test image."

        async def async_iter():
            yield mock_chunk

        mock_provider.send_message.return_value = async_iter()

        with patch.object(tool, "_get_provider", return_value=mock_provider):
            result = await tool.execute(
                ImageAnalyzeInput(image_path=str(image_file), prompt="Describe"),
                ctx,
            )

        assert result.is_error is False
        assert "test image" in result.output

    @pytest.mark.asyncio
    async def test_analyze_with_url(self, tmp_path: Path):
        tool = ImageAnalyze()
        ctx = ToolExecutionContext(cwd=tmp_path)

        mock_provider = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.text = "A cat photo."

        async def async_iter():
            yield mock_chunk

        mock_provider.send_message.return_value = async_iter()

        with patch.object(tool, "_get_provider", return_value=mock_provider):
            result = await tool.execute(
                ImageAnalyzeInput(image_url="https://example.com/cat.jpg", prompt="What animal?"),
                ctx,
            )

        assert result.is_error is False
        assert "cat" in result.output.lower()

    @pytest.mark.asyncio
    async def test_analyze_file_not_found(self, tmp_path: Path):
        tool = ImageAnalyze()
        ctx = ToolExecutionContext(cwd=tmp_path)

        result = await tool.execute(
            ImageAnalyzeInput(image_path="/nonexistent/image.png", prompt="Describe"),
            ctx,
        )

        assert result.is_error is True
        assert "not found" in result.output.lower()

    @pytest.mark.asyncio
    async def test_analyze_no_image_source(self, tmp_path: Path):
        tool = ImageAnalyze()
        ctx = ToolExecutionContext(cwd=tmp_path)

        result = await tool.execute(
            ImageAnalyzeInput(prompt="Describe"),
            ctx,
        )

        assert result.is_error is True
        assert "image_path or image_url" in result.output.lower()

    @pytest.mark.asyncio
    async def test_analyze_provider_error(self, tmp_path: Path):
        tool = ImageAnalyze()
        ctx = ToolExecutionContext(cwd=tmp_path)

        image_file = tmp_path / "test.png"
        image_file.write_bytes(b"fake png data")

        mock_provider = MagicMock()

        async def raise_error(*a, **k):
            raise Exception("API error")

        mock_provider.send_message.side_effect = raise_error

        with patch.object(tool, "_get_provider", return_value=mock_provider):
            result = await tool.execute(
                ImageAnalyzeInput(image_path=str(image_file), prompt="Describe"),
                ctx,
            )

        assert result.is_error is True
        assert "api error" in result.output.lower()

    def test_encode_image_base64(self, tmp_path: Path):
        tool = ImageAnalyze()
        image_file = tmp_path / "test.bin"
        image_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        encoded = tool._encode_image_base64(image_file)
        assert len(encoded) > 0
        # Verify it's valid base64 by decoding
        decoded = base64.b64decode(encoded)
        assert decoded == b"\x89PNG\r\n\x1a\n"

    def test_detect_mime_type(self):
        tool = ImageAnalyze()
        assert tool._detect_mime_type("test.png") == "image/png"
        assert tool._detect_mime_type("test.jpg") == "image/jpeg"
        assert tool._detect_mime_type("test.jpeg") == "image/jpeg"
        assert tool._detect_mime_type("test.gif") == "image/gif"
        assert tool._detect_mime_type("test.webp") == "image/webp"
        assert tool._detect_mime_type("test.unknown") == "image/png"
