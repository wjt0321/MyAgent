"""Permission checker for MyAgent."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class PermissionLevel(IntEnum):
    """Permission decision levels."""

    ALLOW = 1
    ASK = 2
    DENY = 3


@dataclass
class PermissionResult:
    """Result of a permission check."""

    level: PermissionLevel
    reason: str


# Tools that are read-only by default
READ_ONLY_TOOLS = {"Read", "Glob", "Grep", "WebFetch", "WebSearch"}

# Tools that modify state
WRITE_TOOLS = {"Write", "Edit", "Bash", "AgentTool", "TodoWrite"}

# Dangerous command patterns (auto-deny)
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+[~.]?/",
    r"sudo\s+",
    r">\s*/dev/",
    r"mkfs\.",
    r"dd\s+if=",
    r"chmod\s+-R\s+777",
    r"curl\s+.*\|\s*sh",
    r"wget\s+.*\|\s*sh",
]

# Sensitive file patterns (ask before reading)
SENSITIVE_FILE_PATTERNS = [
    "*.env*",
    "*.key",
    "*.pem",
    "*.p12",
    "*.pfx",
    "*password*",
    "*secret*",
    "*token*",
    "*credential*",
]

# Files that should never be read (auto-deny)
FORBIDDEN_FILE_PATTERNS = [
    "*.ssh/id_rsa*",
    "*.ssh/id_ed25519*",
    "*.ssh/id_ecdsa*",
    "*.ssh/id_dsa*",
    "*.gnupg/secring*",
    "*.aws/credentials",
    "*kube/config",
]


class PermissionChecker:
    """Checks permissions for tool execution."""

    def __init__(
        self,
        default_level: PermissionLevel = PermissionLevel.ASK,
        rules: dict[str, PermissionLevel] | None = None,
    ) -> None:
        self.default_level = default_level
        self._rules: dict[str, PermissionLevel] = rules or {}
        self._allow_list: set[str] = set()
        self._deny_list: set[str] = set()
        self._once_approved: set[str] = set()

    def check(self, tool_name: str, arguments: dict[str, Any]) -> PermissionResult:
        """Check if a tool execution is permitted."""
        # Check explicit deny list
        if tool_name in self._deny_list:
            return PermissionResult(PermissionLevel.DENY, f"Tool '{tool_name}' is in deny list")

        # Check explicit allow list
        if tool_name in self._allow_list:
            return PermissionResult(PermissionLevel.ALLOW, f"Tool '{tool_name}' is in allow list")

        # Check one-time approvals
        args_key = self._args_key(tool_name, arguments)
        if args_key in self._once_approved:
            return PermissionResult(PermissionLevel.ALLOW, "One-time approved")

        # Check custom rules
        if tool_name in self._rules:
            level = self._rules[tool_name]
            reason = f"Custom rule: {level.name}"
            return PermissionResult(level, reason)

        # Read-only tools are generally safe
        if tool_name in READ_ONLY_TOOLS:
            # But check for sensitive files
            path = self._extract_path(arguments)
            if path:
                if self._is_forbidden_file(path):
                    return PermissionResult(
                        PermissionLevel.DENY,
                        f"Access to SSH/private key file denied: {path}",
                    )
                if self._is_sensitive_file(path):
                    return PermissionResult(
                        PermissionLevel.ASK,
                        f"Sensitive file access requires approval: {path}",
                    )
            return PermissionResult(PermissionLevel.ALLOW, "Read-only tool")

        # Check Bash for dangerous commands
        if tool_name == "Bash":
            command = arguments.get("command", "")
            if self._is_dangerous_command(command):
                return PermissionResult(
                    PermissionLevel.DENY,
                    f"Dangerous command detected: {command[:50]}",
                )
            return PermissionResult(
                PermissionLevel.ASK,
                "Bash command requires approval",
            )

        # Write tools require approval
        if tool_name in WRITE_TOOLS:
            return PermissionResult(
                PermissionLevel.ASK,
                f"Write tool '{tool_name}' requires approval",
            )

        # Unknown tools default to ASK
        return PermissionResult(
            PermissionLevel.ASK,
            f"Unknown tool '{tool_name}' - approval required",
        )

    def is_approved(self, tool_name: str, arguments: dict[str, Any]) -> bool:
        """Check if a specific tool call is already approved."""
        result = self.check(tool_name, arguments)
        return result.level == PermissionLevel.ALLOW

    def allow_tool(self, tool_name: str) -> None:
        """Permanently allow a tool."""
        self._allow_list.add(tool_name)
        self._deny_list.discard(tool_name)

    def deny_tool(self, tool_name: str) -> None:
        """Permanently deny a tool."""
        self._deny_list.add(tool_name)
        self._allow_list.discard(tool_name)

    def approve_once(self, tool_name: str, arguments: dict[str, Any]) -> None:
        """Approve a specific tool call once."""
        self._once_approved.add(self._args_key(tool_name, arguments))

    def _args_key(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Generate a key for tracking one-time approvals."""
        import json

        sorted_args = dict(sorted(arguments.items()))
        return f"{tool_name}:{json.dumps(sorted_args, sort_keys=True)}"

    def _extract_path(self, arguments: dict[str, Any]) -> str | None:
        """Extract file path from tool arguments."""
        for key in ("path", "file", "filepath", "target"):
            if key in arguments:
                return str(arguments[key])
        return None

    def _is_dangerous_command(self, command: str) -> bool:
        """Check if a bash command is dangerous."""
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False

    def _is_sensitive_file(self, path: str) -> bool:
        """Check if a file path matches sensitive patterns."""
        name = path.split("/")[-1].split("\\")[-1]
        for pattern in SENSITIVE_FILE_PATTERNS:
            if fnmatch.fnmatch(name.lower(), pattern.lower()):
                return True
        return False

    def _is_forbidden_file(self, path: str) -> bool:
        """Check if a file path matches forbidden patterns."""
        for pattern in FORBIDDEN_FILE_PATTERNS:
            if fnmatch.fnmatch(path.lower(), pattern.lower()):
                return True
        return False
