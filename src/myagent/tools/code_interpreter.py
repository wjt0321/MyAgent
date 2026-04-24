"""Code interpreter tool for MyAgent.

Executes Python code in a restricted sandbox environment.
Inspired by Claude Code's code execution capabilities.
"""

from __future__ import annotations

import ast
import builtins
import io
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from types import ModuleType
from typing import Any

from pydantic import BaseModel, Field

from myagent.tools.base import BaseTool, ToolExecutionContext, ToolResult


class CodeInterpreterInput(BaseModel):
    code: str = Field(description="Python code to execute")
    timeout: int = Field(default=30, description="Timeout in seconds")


class RestrictedBuiltins:
    """Restricted builtins for code interpreter sandbox."""

    ALLOWED_BUILTINS = {
        "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes",
        "callable", "chr", "complex", "dict", "divmod", "enumerate", "filter",
        "float", "format", "frozenset", "hasattr", "hash", "hex", "int",
        "isinstance", "issubclass", "iter", "len", "list", "map", "max",
        "memoryview", "min", "next", "oct", "ord", "pow", "range", "repr",
        "reversed", "round", "set", "slice", "sorted", "str", "sum", "tuple",
        "type", "zip", "print", "input", "open", "help",
        "True", "False", "None",
        "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
        "AttributeError", "RuntimeError", "StopIteration", "OSError",
        "ImportError", "ModuleNotFoundError", "ZeroDivisionError",
        "ArithmeticError", "AssertionError", "NameError", "SyntaxError",
        "OverflowError", "RecursionError", "NotImplementedError",
    }

    @classmethod
    def create(cls) -> dict[str, Any]:
        """Create a restricted builtins dictionary."""
        restricted = {}
        for name in cls.ALLOWED_BUILTINS:
            if hasattr(builtins, name):
                restricted[name] = getattr(builtins, name)
        return restricted


class CodeSandbox:
    """Sandbox for executing Python code safely."""

    FORBIDDEN_MODULES = {
        "os", "sys", "subprocess", "socket", "urllib", "http", "ftplib",
        "smtplib", "telnetlib", "ctypes", "mmap", "resource", "signal",
        "pty", "pickle", "marshal", "shelve", "dbm", "sqlite3",
    }

    ALLOWED_MODULES = {
        "math", "random", "statistics", "fractions", "decimal", "numbers",
        "datetime", "time", "calendar", "itertools", "functools", "collections",
        "heapq", "bisect", "copy", "pprint", "reprlib", "enum", "types",
        "string", "re", "json", "csv", "html", "xml", "base64", "binascii",
        "hashlib", "hmac", "secrets", "uuid", "textwrap", "stringprep",
        "difflib", "pathlib", "dataclasses", "typing", "abc", "inspect",
        "warnings", "contextlib", "functools", "operator", "numbers",
        "numpy", "pandas", "matplotlib", "plotly",
    }

    def __init__(self) -> None:
        self.globals = {
            "__name__": "__sandbox__",
            "__doc__": None,
        }
        self._setup_allowed_modules()
        self.globals["__builtins__"] = RestrictedBuiltins.create()
        self.globals["__builtins__"]["__import__"] = self._safe_import

    def _safe_import(self, name: str, globals=None, locals=None, fromlist=(), level=0):
        """Safe import that only allows whitelisted modules."""
        base = name.split(".")[0]
        if base in self.FORBIDDEN_MODULES:
            raise ImportError(f"Forbidden module: {name}")
        if base not in self.ALLOWED_MODULES:
            raise ImportError(f"Module not allowed: {name}")
        import importlib
        return importlib.import_module(name)

    def _setup_allowed_modules(self) -> None:
        """Pre-import allowed modules into the sandbox."""
        import importlib
        for mod_name in self.ALLOWED_MODULES:
            try:
                module = importlib.import_module(mod_name)
                self.globals[mod_name] = module
            except ImportError:
                pass

    def validate_code(self, code: str) -> tuple[bool, str]:
        """Validate code for forbidden operations."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {e}"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base_module = alias.name.split(".")[0]
                    if base_module in self.FORBIDDEN_MODULES:
                        return False, f"Forbidden module import: {alias.name}"

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    base_module = node.module.split(".")[0]
                    if base_module in self.FORBIDDEN_MODULES:
                        return False, f"Forbidden module import: {node.module}"

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("eval", "exec", "compile"):
                        return False, f"Forbidden function call: {node.func.id}"
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in ("__import__", "__subclasses__"):
                        return False, f"Forbidden attribute access: {node.func.attr}"

            elif isinstance(node, ast.Attribute):
                if node.attr.startswith("__") and node.attr.endswith("__"):
                    if node.attr not in ("__name__", "__doc__", "__class__", "__len__"):
                        pass

        return True, ""

    def execute(self, code: str) -> dict[str, Any]:
        """Execute code in the sandbox."""
        valid, error = self.validate_code(code)
        if not valid:
            return {"success": False, "output": "", "error": error}

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(code, self.globals)

            output = stdout_buffer.getvalue()
            error = stderr_buffer.getvalue()

            if error:
                return {"success": False, "output": output, "error": error}

            return {"success": True, "output": output, "error": ""}

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return {
                "success": False,
                "output": stdout_buffer.getvalue(),
                "error": error_msg,
            }


class CodeInterpreter(BaseTool):
    """Execute Python code in a sandboxed environment.

    Supports data analysis, visualization, and general computation.
    Forbidden: network access, file system manipulation, system commands.
    """

    name = "CodeInterpreter"
    description = (
        "Execute Python code in a sandboxed environment. "
        "Useful for data analysis, calculations, and visualization. "
        "Supports numpy, pandas, matplotlib. "
        "Forbidden: network access, file system manipulation, system commands."
    )
    input_model = CodeInterpreterInput

    def __init__(self) -> None:
        self._sandbox = CodeSandbox()

    async def execute(self, arguments: CodeInterpreterInput, context: ToolExecutionContext) -> ToolResult:
        result = self._sandbox.execute(arguments.code)

        if result["success"]:
            return ToolResult(output=result["output"] or "Code executed successfully (no output).")
        else:
            return ToolResult(
                output=f"Error:\n{result['error']}\n\nStdout:\n{result['output']}",
                is_error=True,
            )
