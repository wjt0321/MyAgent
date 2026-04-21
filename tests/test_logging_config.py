"""Tests for logging configuration."""

from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path

import pytest

from myagent.logging_config import (
    JSONFormatter,
    ColoredFormatter,
    setup_logging,
)


class TestJSONFormatter:
    def test_basic_format(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=1,
            msg="Hello",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["message"] == "Hello"
        assert data["level"] == "INFO"
        assert "timestamp" in data

    def test_extra_fields(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=1,
            msg="Hello",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"
        output = formatter.format(record)
        data = json.loads(output)
        assert data["custom_field"] == "custom_value"

    def test_exception(self):
        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )
        output = formatter.format(record)
        data = json.loads(output)
        assert "exception" in data
        assert "Test error" in data["exception"]


class TestColoredFormatter:
    def test_format(self):
        formatter = ColoredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=1,
            msg="Hello",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "Hello" in output
        assert "INFO" in output


class TestSetupLogging:
    def test_console_only(self):
        setup_logging(level="DEBUG", enable_console=True)
        logger = logging.getLogger("test_console")
        # Should not raise
        logger.info("Test message")

    def test_file_logging(self):
        tmpdir = tempfile.mkdtemp()
        log_file = Path(tmpdir) / "test.log"
        try:
            setup_logging(level="DEBUG", log_file=log_file, enable_console=False)
            logger = logging.getLogger("test_file")
            logger.info("Test file message")

            # Force flush and close handlers
            for handler in logging.getLogger().handlers[:]:
                handler.flush()
                handler.close()
                logging.getLogger().removeHandler(handler)

            assert log_file.exists()
            content = log_file.read_text()
            assert "Test file message" in content
        finally:
            # Clean up
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_json_file_logging(self):
        tmpdir = tempfile.mkdtemp()
        log_file = Path(tmpdir) / "test.json"
        try:
            setup_logging(
                level="DEBUG",
                log_file=log_file,
                json_format=True,
                enable_console=False,
            )
            logger = logging.getLogger("test_json")
            logger.info("Test JSON message")

            # Force flush and close handlers
            for handler in logging.getLogger().handlers[:]:
                handler.flush()
                handler.close()
                logging.getLogger().removeHandler(handler)

            content = log_file.read_text().strip()
            data = json.loads(content)
            assert data["message"] == "Test JSON message"
            assert data["level"] == "INFO"
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_log_rotation(self):
        tmpdir = tempfile.mkdtemp()
        log_file = Path(tmpdir) / "test.log"
        try:
            setup_logging(
                level="DEBUG",
                log_file=log_file,
                max_bytes=100,
                backup_count=2,
                enable_console=False,
            )
            logger = logging.getLogger("test_rotation")

            # Write enough to trigger rotation
            for i in range(20):
                logger.info(f"Message {i}: " + "x" * 50)

            # Force flush and close handlers
            for handler in logging.getLogger().handlers[:]:
                handler.flush()
                handler.close()
                logging.getLogger().removeHandler(handler)

            # Should have backup files
            assert log_file.exists()
            backup_files = list(Path(tmpdir).glob("test.log.*"))
            assert len(backup_files) > 0
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
