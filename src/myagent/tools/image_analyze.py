"""ImageAnalyze tool for MyAgent."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class ImageAnalyzeInput(BaseModel):
    image_path: str | None = Field(default=None, description="Local path to the image file")
    image_url: str | None = Field(default=None, description="URL of the image")
    prompt: str = Field(
        default="Describe what you see in this image.",
        description="Question or prompt about the image",
    )
    model: str | None = Field(default=None, description="Optional vision model override")


class ImageAnalyze(BaseTool):
    name = "ImageAnalyze"
    description = (
        "Analyze an image using a vision-capable LLM. "
        "Provide either a local image_path or an image_url. "
        "Returns a description or analysis of the image content."
    )
    input_model = ImageAnalyzeInput

    def __init__(self, llm_client: Any | None = None) -> None:
        self.llm_client = llm_client

    async def execute(
        self, arguments: ImageAnalyzeInput, context: ToolExecutionContext
    ) -> ToolResult:
        if not arguments.image_path and not arguments.image_url:
            return ToolResult(
                output="Error: Either image_path or image_url must be provided.",
                is_error=True,
            )

        try:
            if arguments.image_path:
                image_path = Path(arguments.image_path)
                if not image_path.exists():
                    return ToolResult(
                        output=f"Error: Image file not found: {arguments.image_path}",
                        is_error=True,
                    )

                mime_type = self._detect_mime_type(arguments.image_path)
                base64_data = self._encode_image_base64(image_path)
                image_content = f"data:{mime_type};base64,{base64_data}"
            else:
                image_content = arguments.image_url

            provider = self._get_provider()
            if provider is None:
                return ToolResult(
                    output="Error: No vision-capable LLM provider available.",
                    is_error=True,
                )

            messages = self._build_messages(image_content, arguments.prompt)

            output_parts: list[str] = []
            response = provider.send_message(messages)
            if hasattr(response, "__aiter__"):
                async for chunk in response:
                    if hasattr(chunk, "text"):
                        output_parts.append(chunk.text)
            else:
                result_text = await response if hasattr(response, "__await__") else str(response)
                output_parts.append(result_text)

            result = "".join(output_parts) or "No analysis generated."
            return ToolResult(output=result)

        except Exception as e:
            return ToolResult(
                output=f"Error analyzing image: {e}",
                is_error=True,
            )

    def _build_messages(self, image_content: str, prompt: str) -> list[dict[str, Any]]:
        """Build messages with image for vision model."""
        is_url = image_content.startswith("http")

        if is_url:
            image_data = {"type": "image_url", "image_url": {"url": image_content}}
        else:
            image_data = {"type": "image_url", "image_url": {"url": image_content}}

        return [
            {
                "role": "user",
                "content": [
                    image_data,
                    {"type": "text", "text": prompt},
                ],
            }
        ]

    def _encode_image_base64(self, path: Path) -> str:
        """Encode image file to base64 string."""
        data = path.read_bytes()
        return base64.b64encode(data).decode("utf-8")

    def _detect_mime_type(self, path: str) -> str:
        """Detect MIME type from file extension."""
        ext = Path(path).suffix.lower()
        mapping = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
            ".svg": "image/svg+xml",
        }
        return mapping.get(ext, "image/png")

    def _get_provider(self) -> Any | None:
        """Get a vision-capable LLM provider."""
        if self.llm_client is not None:
            return self.llm_client
        return None

    def is_read_only(self, arguments: BaseModel) -> bool:
        return True
