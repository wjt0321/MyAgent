"""TextToSpeech tool for MyAgent."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class TextToSpeechInput(BaseModel):
    text: str = Field(description="Text to convert to speech")
    output_path: str | None = Field(default=None, description="Output audio file path")
    voice: str = Field(default="default", description="Voice identifier")
    speed: float = Field(default=1.0, description="Speech speed multiplier")


class TextToSpeech(BaseTool):
    name = "TextToSpeech"
    description = (
        "Convert text to speech audio. "
        "Returns the path to the generated audio file. "
        "Supports various voices and speed adjustment."
    )
    input_model = TextToSpeechInput

    def __init__(self, tts_provider: Any | None = None) -> None:
        self.tts_provider = tts_provider

    async def execute(
        self, arguments: TextToSpeechInput, context: ToolExecutionContext
    ) -> ToolResult:
        text = arguments.text.strip()
        if not text:
            return ToolResult(
                output="Error: Text cannot be empty.",
                is_error=True,
            )

        provider = self._get_provider()
        if provider is None:
            return ToolResult(
                output="Error: No TTS provider available.",
                is_error=True,
            )

        try:
            audio_data = provider.synthesize(
                text=text,
                voice=arguments.voice,
                speed=arguments.speed,
            )

            if isinstance(audio_data, bytes):
                output_path = self._resolve_output_path(arguments.output_path, context.cwd)
                output_path.write_bytes(audio_data)
                return ToolResult(
                    output=f"Audio saved to: {output_path}",
                    metadata={"path": str(output_path), "size": len(audio_data)},
                )
            else:
                return ToolResult(
                    output=f"Error: TTS provider returned invalid data type: {type(audio_data)}",
                    is_error=True,
                )

        except Exception as e:
            return ToolResult(
                output=f"Error synthesizing speech: {e}",
                is_error=True,
            )

    def _get_provider(self) -> Any | None:
        """Get the TTS provider."""
        return self.tts_provider

    def _resolve_output_path(self, output_path: str | None, cwd: Path) -> Path:
        """Resolve the output audio file path."""
        if output_path:
            path = Path(output_path)
            if not path.is_absolute():
                path = cwd / path
            return path

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        unique = uuid.uuid4().hex[:6]
        return cwd / f"speech-{timestamp}-{unique}.mp3"

    def is_read_only(self, arguments: BaseModel) -> bool:
        return False
