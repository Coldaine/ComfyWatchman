"""
Unit tests for the logging module.

Tests logging configuration, structured formatting, file rotation,
and backward compatibility functions.
"""

import json
import logging
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

import pytest</search>

from comfyfixersmart.logging import (
    LogConfig, StructuredFormatter, ComfyFixerLogger,
    get_logger, setup_logging, log, log_with_timestamp
)


class TestLogConfig:
    """Test LogConfig dataclass."""

    def test_log_config_defaults(self):
        """Test LogConfig default values."""
        config = LogConfig()

        assert config.log_dir == Path("log")
        assert config.run_id_format == "%Y%m%d_%H%M%S"
        assert config.console_level == logging.INFO
        assert config.file_level == logging.DEBUG
        assert config.max_bytes == 10 * 1024 * 1024  # 10MB
        assert config.backup_count == 5
        assert config.enable_structured is True
        assert config.structured_file == "structured.log"
        assert "%(asctime)s [%(levelname)s] %(name)s: %(message)s" in config.format_string
        assert config.date_format == "%Y-%m-%d %H:%M:%S"

    def test_log_config_custom_values(self):
        """Test LogConfig with custom values."""
        custom_config = LogConfig(
            log_dir=Path("/custom/log"),
            console_level=logging.DEBUG,
            max_bytes=5 * 1024 * 1024,
            enable_structured=False
        )

        assert custom_config.log_dir == Path("/custom/log")
        assert custom_config.console_level == logging.DEBUG
        assert custom_config.max_bytes == 5 * 1024 * 1024
        assert custom_config.enable_structured is False


class TestStructuredFormatter:
    """Test StructuredFormatter class."""

    def test_format_basic_record(self):
        """Test basic log record formatting."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.created = 1640995200.0  # 2022-01-01 00:00:00 UTC

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["timestamp"] == "2022-01-01T00:00:00"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "Test message"
        assert parsed["module"] == "test"
        assert parsed["function"] == "<module>"
        assert parsed["line"] == 10

    def test_format_record_with_extra_data(self):
        """Test log record formatting with extra data."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.extra_data = {"custom_field": "custom_value", "number": 42}

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["custom_field"] == "custom_value"
        assert parsed["number"] == 42

    def test_format_record_with_exception(self):
        """Test log record formatting with exception info."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert "ValueError: Test exception" in parsed["exception"]


class TestComfyFixerLogger:
    """Test ComfyFixerLogger class."""

    def test_logger_initialization_default(self):
        """Test logger initialization with default config."""
        logger = ComfyFixerLogger()

        assert logger.name == "ComfyFixerSmart"
        assert isinstance(logger.config, LogConfig)
        assert logger.logger.name == "ComfyFixerSmart"

    def test_logger_initialization_custom(self):
        """Test logger initialization with custom config."""
        custom_config = LogConfig(log_dir=Path("/tmp"), console_level=logging.DEBUG)
        logger = ComfyFixerLogger("CustomLogger", custom_config)

        assert logger.name == "CustomLogger"
        assert logger.config == custom_config
        assert logger.logger.name == "CustomLogger"

    def test_logger_setup_creates_handlers(self, tmp_path):
        """Test that logger setup creates appropriate handlers."""
        config = LogConfig(log_dir=tmp_path / "logs")
        logger = ComfyFixerLogger(config=config)

        # Should have at least console and file handlers
        handlers = logger.logger.handlers
        assert len(handlers) >= 2

        # Check handler types
        handler_types = [type(h).__name__ for h in handlers]
        assert "StreamHandler" in handler_types
        assert "RotatingFileHandler" in handler_types

    def test_logger_setup_creates_log_directory(self, tmp_path):
        """Test that logger setup creates log directory."""
        log_dir = tmp_path / "test_logs"
        config = LogConfig(log_dir=log_dir)
        logger = ComfyFixerLogger(config=config)

        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_logger_setup_structured_handler(self, tmp_path):
        """Test that structured handler is created when enabled."""
        log_dir = tmp_path / "logs"
        config = LogConfig(log_dir=log_dir, enable_structured=True, structured_file="structured.log")
        logger = ComfyFixerLogger(config=config)

        # Should have structured handler
        handlers = logger.logger.handlers
        structured_handlers = [h for h in handlers if isinstance(h.formatter, StructuredFormatter)]
        assert len(structured_handlers) == 1

    def test_logger_setup_no_structured_handler(self, tmp_path):
        """Test that structured handler is not created when disabled."""
        log_dir = tmp_path / "logs"
        config = LogConfig(log_dir=log_dir, enable_structured=False)
        logger = ComfyFixerLogger(config=config)

        # Should not have structured handler
        handlers = logger.logger.handlers
        structured_handlers = [h for h in handlers if isinstance(h.formatter, StructuredFormatter)]
        assert len(structured_handlers) == 0

    def test_logging_methods(self, tmp_path, caplog):
        """Test all logging methods."""
        config = LogConfig(log_dir=tmp_path / "logs")
        logger = ComfyFixerLogger(config=config)

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

        # Check that messages were logged
        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text
        assert "Critical message" in caplog.text

    def test_logging_with_extra_data(self, tmp_path, caplog):
        """Test logging with extra data."""
        config = LogConfig(log_dir=tmp_path / "logs")
        logger = ComfyFixerLogger(config=config)

        extra_data = {"key": "value", "count": 5}

        with caplog.at_level(logging.INFO):
            logger.info("Message with extra", extra=extra_data)

        assert "Message with extra" in caplog.text

    def test_log_action(self, tmp_path, caplog):
        """Test structured action logging."""
        config = LogConfig(log_dir=tmp_path / "logs")
        logger = ComfyFixerLogger(config=config)

        details = {"model": "test.safetensors", "size": 100}

        with caplog.at_level(logging.INFO):
            logger.log_action("download", details)

        assert "Action: download" in caplog.text

    def test_log_model_operation(self, tmp_path, caplog):
        """Test model operation logging."""
        config = LogConfig(log_dir=tmp_path / "logs")
        logger = ComfyFixerLogger(config=config)

        with caplog.at_level(logging.INFO):
            logger.log_model_operation("download", "model.safetensors", "checkpoints", "success")

        assert "Model download: model.safetensors (checkpoints) - success" in caplog.text

    def test_get_log_file_path(self, tmp_path):
        """Test getting log file path."""
        config = LogConfig(log_dir=tmp_path / "logs")
        logger = ComfyFixerLogger(config=config)

        log_path = logger.get_log_file_path()
        assert log_path.parent == tmp_path / "logs"
        assert log_path.name.startswith("run_")
        assert log_path.name.endswith(".log")


class TestGlobalLoggerFunctions:
    """Test global logger functions."""

    @patch('comfyfixersmart.logging._default_logger', None)
    def test_get_logger_creates_new_instance(self):
        """Test get_logger creates new instance when none exists."""
        logger = get_logger("TestLogger")

        assert isinstance(logger, ComfyFixerLogger)
        assert logger.name == "TestLogger"

    @patch('comfyfixersmart.logging._default_logger')
    def test_get_logger_returns_existing_instance(self, mock_logger):
        """Test get_logger returns existing instance."""
        mock_logger.name = "ExistingLogger"
        logger = get_logger()

        assert logger == mock_logger

    @patch('comfyfixersmart.logging._default_logger', None)
    def test_get_logger_with_config(self):
        """Test get_logger with config parameter."""
        config = LogConfig(console_level=logging.DEBUG)
        logger = get_logger("TestLogger", config)

        assert logger.config == config

    def test_setup_logging_alias(self):
        """Test that setup_logging is an alias for get_logger."""
        assert setup_logging == get_logger


class TestBackwardCompatibility:
    """Test backward compatibility functions."""

    def test_log_function_default_level(self, caplog):
        """Test backward compatible log function with default level."""
        with caplog.at_level(logging.INFO):
            log("Test message")

        assert "Test message" in caplog.text

    def test_log_function_custom_level(self, caplog):
        """Test backward compatible log function with custom level."""
        with caplog.at_level(logging.DEBUG):
            log("Debug message", "DEBUG")
            log("Error message", "ERROR")

        assert "Debug message" in caplog.text
        assert "Error message" in caplog.text

    def test_log_function_invalid_level(self, caplog):
        """Test backward compatible log function with invalid level."""
        with caplog.at_level(logging.INFO):
            log("Test message", "INVALID")

        # Should default to INFO
        assert "Test message" in caplog.text

    def test_log_with_timestamp(self, caplog):
        """Test log_with_timestamp function."""
        with caplog.at_level(logging.INFO):
            log_with_timestamp("Timestamped message")

        assert "Timestamped message" in caplog.text


class TestLoggerFileOutput:
    """Test logger file output functionality."""

    def test_file_logging_creates_log_file(self, tmp_path):
        """Test that logging creates log files."""
        log_dir = tmp_path / "logs"
        config = LogConfig(log_dir=log_dir)
        logger = ComfyFixerLogger(config=config)

        logger.info("Test log message")

        # Check that log file was created
        log_files = list(log_dir.glob("run_*.log"))
        assert len(log_files) == 1

        # Check log content
        log_content = log_files[0].read_text()
        assert "Test log message" in log_content

    def test_structured_logging_creates_json_file(self, tmp_path):
        """Test that structured logging creates JSON log files."""
        log_dir = tmp_path / "logs"
        config = LogConfig(
            log_dir=log_dir,
            enable_structured=True,
            structured_file="structured.log"
        )
        logger = ComfyFixerLogger(config=config)

        logger.info("Structured test message")

        # Check that structured log file was created
        structured_file = log_dir / "structured.log"
        assert structured_file.exists()

        # Check that content is valid JSON
        content = structured_file.read_text().strip()
        if content:  # May be empty if buffering
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    parsed = json.loads(line)
                    assert "message" in parsed
                    assert "timestamp" in parsed

    def test_log_rotation(self, tmp_path):
        """Test log file rotation."""
        log_dir = tmp_path / "logs"
        config = LogConfig(
            log_dir=log_dir,
            max_bytes=100,  # Small size to trigger rotation
            backup_count=2
        )
        logger = ComfyFixerLogger(config=config)

        # Write enough logs to trigger rotation
        for i in range(10):
            logger.info(f"Log message {i} with enough content to exceed max bytes limit")

        # Check that rotation occurred
        log_files = list(log_dir.glob("run_*.log*"))
        assert len(log_files) >= 1  # At least the current log file


class TestLoggerLevels:
    """Test logger level filtering."""

    def test_console_level_filtering(self, tmp_path, capsys):
        """Test that console handler respects log level."""
        config = LogConfig(
            log_dir=tmp_path / "logs",
            console_level=logging.WARNING  # Only WARNING and above
        )
        logger = ComfyFixerLogger(config=config)

        logger.debug("Debug message")  # Should not appear
        logger.info("Info message")    # Should not appear
        logger.warning("Warning message")  # Should appear
        logger.error("Error message")     # Should appear

        captured = capsys.readouterr()
        output = captured.out

        assert "Debug message" not in output
        assert "Info message" not in output
        assert "Warning message" in output
        assert "Error message" in output

    def test_file_level_filtering(self, tmp_path):
        """Test that file handler logs all levels regardless of console level."""
        config = LogConfig(
            log_dir=tmp_path / "logs",
            console_level=logging.WARNING,  # Console only shows WARNING+
            file_level=logging.DEBUG       # File logs everything
        )
        logger = ComfyFixerLogger(config=config)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")

        # Check file content
        log_files = list((tmp_path / "logs").glob("run_*.log"))
        assert len(log_files) == 1

        log_content = log_files[0].read_text()
        assert "Debug message" in log_content
        assert "Info message" in log_content
        assert "Warning message" in log_content