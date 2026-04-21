"""Tests for PermissionChecker and security infrastructure."""

from pathlib import Path

import pytest

from myagent.security.checker import PermissionChecker, PermissionLevel, PermissionResult


class TestPermissionLevel:
    def test_level_ordering(self):
        assert PermissionLevel.ALLOW < PermissionLevel.ASK
        assert PermissionLevel.ASK < PermissionLevel.DENY
        assert PermissionLevel.ALLOW < PermissionLevel.DENY


class TestPermissionChecker:
    def test_checker_creation(self):
        checker = PermissionChecker()
        assert checker.default_level == PermissionLevel.ASK

    def test_checker_default_allow(self):
        checker = PermissionChecker(default_level=PermissionLevel.ALLOW)
        assert checker.default_level == PermissionLevel.ALLOW

    def test_check_read_only_tool(self):
        checker = PermissionChecker()
        result = checker.check("Read", {"path": "/etc/passwd"})
        assert result.level == PermissionLevel.ALLOW
        assert result.reason == "Read-only tool"

    def test_check_write_tool(self):
        checker = PermissionChecker()
        result = checker.check("Write", {"path": "/tmp/test.txt"})
        assert result.level == PermissionLevel.ASK
        assert "write" in result.reason.lower()

    def test_check_bash_tool(self):
        checker = PermissionChecker()
        result = checker.check("Bash", {"command": "ls -la"})
        assert result.level == PermissionLevel.ASK
        assert "bash" in result.reason.lower()

    def test_check_edit_tool(self):
        checker = PermissionChecker()
        result = checker.check("Edit", {"path": "main.py"})
        assert result.level == PermissionLevel.ASK

    def test_check_dangerous_command(self):
        checker = PermissionChecker()
        result = checker.check("Bash", {"command": "rm -rf /"})
        assert result.level == PermissionLevel.DENY
        assert "dangerous" in result.reason.lower()

    def test_check_sudo_command(self):
        checker = PermissionChecker()
        result = checker.check("Bash", {"command": "sudo apt update"})
        assert result.level == PermissionLevel.DENY

    def test_check_sensitive_file_read(self):
        checker = PermissionChecker()
        result = checker.check("Read", {"path": ".env"})
        assert result.level == PermissionLevel.ASK
        assert "sensitive" in result.reason.lower()

    def test_check_ssh_key_read(self):
        checker = PermissionChecker()
        result = checker.check("Read", {"path": "~/.ssh/id_rsa"})
        assert result.level == PermissionLevel.DENY
        assert "ssh" in result.reason.lower()

    def test_custom_rules(self):
        rules = {
            "Bash": PermissionLevel.DENY,
        }
        checker = PermissionChecker(default_level=PermissionLevel.ALLOW, rules=rules)
        result = checker.check("Bash", {"command": "echo hello"})
        assert result.level == PermissionLevel.DENY

    def test_allow_list(self):
        checker = PermissionChecker()
        checker.allow_tool("Write")
        result = checker.check("Write", {"path": "test.txt"})
        assert result.level == PermissionLevel.ALLOW

    def test_deny_list(self):
        checker = PermissionChecker(default_level=PermissionLevel.ALLOW)
        checker.deny_tool("Bash")
        result = checker.check("Bash", {"command": "echo hello"})
        assert result.level == PermissionLevel.DENY

    def test_approve_once(self):
        checker = PermissionChecker()
        checker.approve_once("Bash", {"command": "ls"})
        result = checker.check("Bash", {"command": "ls"})
        assert result.level == PermissionLevel.ALLOW

    def test_approve_once_different_args(self):
        checker = PermissionChecker()
        checker.approve_once("Bash", {"command": "ls"})
        result = checker.check("Bash", {"command": "pwd"})
        assert result.level == PermissionLevel.ASK

    def test_is_approved(self):
        checker = PermissionChecker()
        assert checker.is_approved("Write", {"path": "test.txt"}) is False
        checker.allow_tool("Write")
        assert checker.is_approved("Write", {"path": "test.txt"}) is True

    def test_check_unknown_tool(self):
        checker = PermissionChecker()
        result = checker.check("UnknownTool", {})
        assert result.level == PermissionLevel.ASK
