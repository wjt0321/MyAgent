"""Tests for LSP client."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from myagent.lsp.client import LSPClient
from myagent.lsp.types import Diagnostic, LSPPosition, LSPRange, TextDocumentItem


class TestLSPPosition:
    def test_position_creation(self):
        pos = LSPPosition(line=10, character=5)
        assert pos.line == 10
        assert pos.character == 5

    def test_position_to_dict(self):
        pos = LSPPosition(line=1, character=2)
        assert pos.to_dict() == {"line": 1, "character": 2}


class TestLSPRange:
    def test_range_creation(self):
        r = LSPRange(start=LSPPosition(0, 0), end=LSPPosition(1, 0))
        assert r.start.line == 0
        assert r.end.line == 1


class TestDiagnostic:
    def test_diagnostic_creation(self):
        d = Diagnostic(
            range=LSPRange(start=LSPPosition(0, 0), end=LSPPosition(0, 5)),
            message="Undefined variable",
            severity=1,
        )
        assert d.message == "Undefined variable"
        assert d.severity == 1


class TestTextDocumentItem:
    def test_document_creation(self):
        doc = TextDocumentItem(
            uri="file:///test.py",
            language_id="python",
            version=1,
            text="print('hello')",
        )
        assert doc.uri == "file:///test.py"
        assert doc.language_id == "python"


class TestLSPClient:
    def test_client_creation(self):
        client = LSPClient(command="pylsp")
        assert client.command == "pylsp"
        assert client._process is None
        assert client._initialized is False

    def test_client_custom_transport(self):
        client = LSPClient(transport="tcp", host="localhost", port=8080)
        assert client.transport == "tcp"
        assert client.host == "localhost"
        assert client.port == 8080

    @pytest.mark.asyncio
    async def test_start_stdio(self):
        client = LSPClient(command="echo")

        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stdin.write = MagicMock()
        mock_proc.stdin.flush = MagicMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            await client.start()

        assert client._process is not None
        client.stop()

    def test_stop(self):
        client = LSPClient()
        mock_proc = MagicMock()
        client._process = mock_proc
        client._initialized = True

        client.stop()

        assert client._process is None
        assert client._initialized is False
        mock_proc.terminate.assert_called_once()

    def test_build_initialize_params(self):
        client = LSPClient()
        params = client._build_initialize_params()
        assert params["processId"] is not None
        assert "capabilities" in params
        assert params["rootUri"] is not None

    def test_build_did_open_params(self):
        client = LSPClient()
        params = client._build_did_open_params("file:///test.py", "python", "print(1)")
        assert params["textDocument"]["uri"] == "file:///test.py"
        assert params["textDocument"]["languageId"] == "python"
        assert params["textDocument"]["text"] == "print(1)"

    def test_build_completion_params(self):
        client = LSPClient()
        params = client._build_completion_params("file:///test.py", LSPPosition(1, 5))
        assert params["textDocument"]["uri"] == "file:///test.py"
        assert params["position"]["line"] == 1
        assert params["position"]["character"] == 5

    def test_parse_diagnostics(self):
        client = LSPClient()
        raw = [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 4},
                },
                "message": "Syntax error",
                "severity": 1,
            }
        ]

        diagnostics = client._parse_diagnostics(raw)
        assert len(diagnostics) == 1
        assert diagnostics[0].message == "Syntax error"
        assert diagnostics[0].severity == 1

    def test_parse_diagnostics_empty(self):
        client = LSPClient()
        diagnostics = client._parse_diagnostics([])
        assert diagnostics == []

    def test_parse_completions(self):
        client = LSPClient()
        raw = {
            "items": [
                {"label": "print", "kind": 3, "detail": "builtin"},
                {"label": "range", "kind": 3},
            ]
        }

        completions = client._parse_completions(raw)
        assert len(completions) == 2
        assert completions[0]["label"] == "print"
        assert completions[0]["detail"] == "builtin"

    def test_parse_completions_plain_list(self):
        client = LSPClient()
        raw = ["print", "range", "len"]

        completions = client._parse_completions(raw)
        assert len(completions) == 3
        assert completions[0]["label"] == "print"

    def test_path_to_uri(self):
        client = LSPClient()
        # Use a relative path that resolves predictably
        uri = client._path_to_uri("test_file.py")
        assert uri.startswith("file://")
        assert "test_file.py" in uri

    def test_path_to_uri_windows(self):
        client = LSPClient()
        uri = client._path_to_uri("C:\\Users\\test.py")
        assert uri == "file:///C:/Users/test.py"
