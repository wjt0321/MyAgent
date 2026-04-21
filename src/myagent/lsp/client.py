"""LSP client for MyAgent."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from myagent.lsp.types import Diagnostic, LSPPosition, LSPRange


class LSPClient:
    """Lightweight LSP client for code intelligence."""

    def __init__(
        self,
        command: str | None = None,
        transport: str = "stdio",
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        self.command = command
        self.transport = transport
        self.host = host
        self.port = port
        self._process: Any | None = None
        self._initialized = False
        self._request_id = 0

    async def start(self) -> None:
        """Start the LSP server connection."""
        if self.transport == "stdio" and self.command:
            import asyncio

            self._process = await asyncio.create_subprocess_exec(
                self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

        self._initialized = True

    def stop(self) -> None:
        """Stop the LSP server connection."""
        if self._process is not None:
            try:
                self._process.terminate()
            except Exception:
                pass
            self._process = None
        self._initialized = False

    def is_initialized(self) -> bool:
        """Check if the client is initialized."""
        return self._initialized

    def _next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    def _build_initialize_params(self) -> dict[str, Any]:
        """Build initialize request params."""
        return {
            "processId": os.getpid(),
            "rootUri": self._path_to_uri(str(Path.cwd())),
            "capabilities": {
                "textDocument": {
                    "synchronization": {"dynamicRegistration": False},
                    "completion": {
                        "dynamicRegistration": False,
                        "completionItem": {"snippetSupport": True},
                    },
                    "hover": {"dynamicRegistration": False},
                    "definition": {"dynamicRegistration": False},
                    "diagnostic": {"dynamicRegistration": False},
                }
            },
        }

    def _build_did_open_params(self, uri: str, language_id: str, text: str) -> dict[str, Any]:
        """Build textDocument/didOpen params."""
        return {
            "textDocument": {
                "uri": uri,
                "languageId": language_id,
                "version": 1,
                "text": text,
            }
        }

    def _build_completion_params(self, uri: str, position: LSPPosition) -> dict[str, Any]:
        """Build textDocument/completion params."""
        return {
            "textDocument": {"uri": uri},
            "position": position.to_dict(),
        }

    def _build_definition_params(self, uri: str, position: LSPPosition) -> dict[str, Any]:
        """Build textDocument/definition params."""
        return {
            "textDocument": {"uri": uri},
            "position": position.to_dict(),
        }

    def _build_did_change_params(self, uri: str, text: str, version: int) -> dict[str, Any]:
        """Build textDocument/didChange params."""
        return {
            "textDocument": {"uri": uri, "version": version},
            "contentChanges": [{"text": text}],
        }

    def _parse_diagnostics(self, raw: list[dict[str, Any]]) -> list[Diagnostic]:
        """Parse raw diagnostics into Diagnostic objects."""
        diagnostics: list[Diagnostic] = []
        for item in raw:
            try:
                range_data = item.get("range", {})
                start = range_data.get("start", {})
                end = range_data.get("end", {})
                diagnostics.append(
                    Diagnostic(
                        range=LSPRange(
                            start=LSPPosition(
                                line=start.get("line", 0),
                                character=start.get("character", 0),
                            ),
                            end=LSPPosition(
                                line=end.get("line", 0),
                                character=end.get("character", 0),
                            ),
                        ),
                        message=item.get("message", ""),
                        severity=item.get("severity"),
                        code=str(item.get("code", "")) if item.get("code") else None,
                        source=item.get("source"),
                    )
                )
            except Exception:
                continue
        return diagnostics

    def _parse_completions(self, raw: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
        """Parse completion response."""
        if isinstance(raw, list):
            return [{"label": str(item)} for item in raw]

        items = raw.get("items", [])
        return [
            {
                "label": item.get("label", ""),
                "kind": item.get("kind"),
                "detail": item.get("detail"),
                "documentation": item.get("documentation"),
            }
            for item in items
        ]

    def _path_to_uri(self, path: str) -> str:
        """Convert file path to URI."""
        abs_path = str(Path(path).resolve())
        if os.name == "nt":
            abs_path = abs_path.replace("\\", "/")
            if not abs_path.startswith("/"):
                abs_path = "/" + abs_path
        return f"file://{abs_path}"

    def _uri_to_path(self, uri: str) -> str:
        """Convert URI to file path."""
        if uri.startswith("file://"):
            path = uri[7:]
            if os.name == "nt" and path.startswith("/"):
                path = path[1:]
            return path
        return uri
