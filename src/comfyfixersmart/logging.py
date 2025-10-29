"""
Unified Logging Module for ComfyFixerSmart

Provides standardized logging across all ComfyFixerSmart components with:
- Consistent log formatting and rotation
- Multiple output destinations (console, file, structured JSON)
- Per-run log files with consistent naming
- Structured logging for better parsing and analysis
- Configurable log levels and destinations
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field


@dataclass
class LogConfig:
    """Configuration for logging setup."""

    log_dir: Path = Path("log")
    run_id_format: str = "%Y%m%d_%H%M%S"
    console_level: int = logging.INFO
    file_level: int = logging.DEBUG
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_structured: bool = True
    structured_file: Optional[str] = "structured.log"
    format_string: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class ComfyFixerLogger:
    """Unified logger for ComfyFixerSmart applications."""

    def __init__(self, name: str = "ComfyFixerSmart", config: Optional[LogConfig] = None):
        self.name = name
        self.config = config or LogConfig()
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """Set up the logger with handlers and formatters."""
        # Clear existing handlers
        self.logger.handlers.clear()

        # Set logger level to lowest level to allow handler filtering
        self.logger.setLevel(logging.DEBUG)

        # Create formatters
        standard_formatter = logging.Formatter(
            self.config.format_string, datefmt=self.config.date_format
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.config.console_level)
        console_handler.setFormatter(standard_formatter)
        self.logger.addHandler(console_handler)

        # File handler with rotation
        self.config.log_dir.mkdir(exist_ok=True)
        run_id = datetime.now().strftime(self.config.run_id_format)
        log_file = self.config.log_dir / f"run_{run_id}.log"

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(self.config.file_level)
        file_handler.setFormatter(standard_formatter)
        self.logger.addHandler(file_handler)

        # Structured JSON handler (optional)
        if self.config.enable_structured and self.config.structured_file:
            structured_file = self.config.log_dir / self.config.structured_file
            structured_handler = logging.handlers.RotatingFileHandler(
                structured_file,
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count,
                encoding="utf-8",
            )
            structured_handler.setLevel(logging.DEBUG)
            structured_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(structured_handler)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log(logging.DEBUG, message, extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log(logging.INFO, message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log(logging.WARNING, message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message."""
        self._log(logging.ERROR, message, extra)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message."""
        self._log(logging.CRITICAL, message, extra)

    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """Internal logging method."""
        if extra:
            # Add extra data to the log record
            extra_data = {"extra_data": extra}
            self.logger.log(level, message, extra=extra_data)
        else:
            self.logger.log(level, message)

    def log_action(self, action: str, details: Dict[str, Any], level: int = logging.INFO):
        """Log a structured action with details."""
        message = f"Action: {action}"
        extra = {"action": action, **details}
        self._log(level, message, extra)

    def log_model_operation(
        self,
        operation: str,
        model_name: str,
        model_type: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log model-related operations."""
        message = f"Model {operation}: {model_name} ({model_type}) - {status}"
        extra = {
            "operation": operation,
            "model_name": model_name,
            "model_type": model_type,
            "status": status,
        }
        if details:
            extra.update(details)
        self._log(logging.INFO, message, extra)

    def get_log_file_path(self) -> Path:
        """Get the current log file path."""
        run_id = datetime.now().strftime(self.config.run_id_format)
        return self.config.log_dir / f"run_{run_id}.log"


# Global logger instance
_default_logger: Optional[ComfyFixerLogger] = None


def get_logger(
    name: str = "ComfyFixerSmart", config: Optional[LogConfig] = None
) -> ComfyFixerLogger:
    """Get or create a logger instance."""
    global _default_logger
    if _default_logger is None or (config and config != _default_logger.config):
        _default_logger = ComfyFixerLogger(name, config)
    return _default_logger


def setup_logging(
    name: str = "ComfyFixerSmart", config: Optional[LogConfig] = None
) -> ComfyFixerLogger:
    """Set up and return a configured logger. Alias for get_logger."""
    return get_logger(name, config)


# Backward compatibility functions
def log(message: str, level: str = "INFO"):
    """Backward compatible log function for existing scripts."""
    logger = get_logger()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    logger._log(level_map.get(level.upper(), logging.INFO), message)


def log_with_timestamp(message: str):
    """Backward compatible function that adds timestamp (now handled by formatter)."""
    log(message)
