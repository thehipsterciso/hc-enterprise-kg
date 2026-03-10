"""Tests for centralized logging configuration."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from cli.logging_config import JsonFormatter, configure_logging

if TYPE_CHECKING:
    from pathlib import Path


class TestConfigureLogging:
    """Tests for configure_logging()."""

    def _reset_root_logger(self) -> None:
        root = logging.getLogger()
        for h in root.handlers[:]:
            root.removeHandler(h)
        root.setLevel(logging.WARNING)

    def test_sets_root_level(self):
        self._reset_root_logger()
        configure_logging(level="DEBUG")
        assert logging.getLogger().level == logging.DEBUG
        self._reset_root_logger()

    def test_default_level_is_info(self):
        self._reset_root_logger()
        configure_logging()
        assert logging.getLogger().level == logging.INFO
        self._reset_root_logger()

    def test_adds_console_handler(self):
        self._reset_root_logger()
        configure_logging()
        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.StreamHandler)
        self._reset_root_logger()

    def test_json_format_uses_json_formatter(self):
        self._reset_root_logger()
        configure_logging(json_format=True)
        root = logging.getLogger()
        assert isinstance(root.handlers[0].formatter, JsonFormatter)
        self._reset_root_logger()

    def test_text_format_uses_standard_formatter(self):
        self._reset_root_logger()
        configure_logging(json_format=False)
        root = logging.getLogger()
        assert isinstance(root.handlers[0].formatter, logging.Formatter)
        assert not isinstance(root.handlers[0].formatter, JsonFormatter)
        self._reset_root_logger()

    def test_file_handler_created(self, tmp_path: Path):
        self._reset_root_logger()
        log_file = str(tmp_path / "test.log")
        configure_logging(log_file=log_file)
        root = logging.getLogger()
        assert len(root.handlers) == 2
        file_handler = root.handlers[1]
        assert isinstance(file_handler, logging.FileHandler)
        self._reset_root_logger()

    def test_env_var_level(self, monkeypatch: object):
        self._reset_root_logger()
        import os

        monkeypatch.setattr(os, "environ", {**os.environ, "HCKG_LOG_LEVEL": "DEBUG"})  # type: ignore[attr-defined]
        configure_logging()
        assert logging.getLogger().level == logging.DEBUG
        self._reset_root_logger()

    def test_reconfigure_removes_old_handlers(self):
        self._reset_root_logger()
        configure_logging()
        configure_logging()
        root = logging.getLogger()
        assert len(root.handlers) == 1
        self._reset_root_logger()


class TestJsonFormatter:
    """Tests for the JSON log formatter."""

    def test_output_is_valid_json(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="hello %s",
            args=("world",),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["message"] == "hello world"
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert "timestamp" in data

    def test_includes_extra_fields(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="req",
            args=(),
            exc_info=None,
        )
        record.method = "GET"  # type: ignore[attr-defined]
        record.path = "/health"  # type: ignore[attr-defined]
        record.status = 200  # type: ignore[attr-defined]
        record.duration_ms = 12.5  # type: ignore[attr-defined]
        output = formatter.format(record)
        data = json.loads(output)
        assert data["method"] == "GET"
        assert data["path"] == "/health"
        assert data["status"] == 200
        assert data["duration_ms"] == 12.5

    def test_includes_exception(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="fail",
                args=(),
                exc_info=sys.exc_info(),
            )
        output = formatter.format(record)
        data = json.loads(output)
        assert "exception" in data
        assert "ValueError: boom" in data["exception"]
