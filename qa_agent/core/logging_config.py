"""Logging configuration for the QA Agent system."""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger


class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """
        Add custom fields to log record.
        
        Args:
            log_record: Dictionary to add fields to
            record: Original log record
            message_dict: Message dictionary
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record["timestamp"] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record["level"] = record.levelname
        
        # Add logger name
        log_record["logger"] = record.name
        
        # Add module and function info
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields from extra
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding context to log messages."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process log message and add extra fields.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Tuple of (message, kwargs)
        """
        # Extract extra fields from kwargs
        extra = kwargs.get("extra", {})
        
        # Add context from adapter
        if self.extra:
            extra.update(self.extra)
        
        kwargs["extra"] = {"extra_fields": extra}
        
        return msg, kwargs


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_file: Optional[Path] = None,
    log_to_console: bool = True,
    json_format: bool = False,
) -> None:
    """
    Set up logging configuration for the QA Agent.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_file: Path to log file (default: output/logs/qa_agent.log)
        log_to_console: Whether to log to console
        json_format: Whether to use JSON format for logs
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if json_format:
        formatter = StructuredFormatter(
            "%(timestamp)s %(level)s %(logger)s %(module)s %(function)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    # Add console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler
    if log_to_file:
        if log_file is None:
            log_file = Path("output/logs/qa_agent.log")
        
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        
        # Always use JSON format for file logs for CI/CD parsing
        if json_format or True:  # Force JSON for file logs
            file_formatter = StructuredFormatter(
                "%(timestamp)s %(level)s %(logger)s %(module)s %(function)s %(message)s"
            )
            file_handler.setFormatter(file_formatter)
        else:
            file_handler.setFormatter(formatter)
        
        root_logger.addHandler(file_handler)
    
    # Set logging level for third-party libraries
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Log initial message
    root_logger.info(
        "Logging initialized",
        extra={
            "log_level": log_level,
            "log_to_file": log_to_file,
            "log_to_console": log_to_console,
            "json_format": json_format,
        },
    )


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> LoggerAdapter:
    """
    Get a logger with optional context.
    
    Args:
        name: Logger name (typically __name__)
        context: Optional context dictionary to add to all log messages
        
    Returns:
        LoggerAdapter instance
    """
    logger = logging.getLogger(name)
    
    if context:
        return LoggerAdapter(logger, context)
    
    return LoggerAdapter(logger, {})


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    message: str = "An error occurred",
    level: int = logging.ERROR,
    **extra_fields: Any,
) -> None:
    """
    Log an exception with structured information.
    
    Args:
        logger: Logger instance
        exception: Exception to log
        message: Log message
        level: Log level
        **extra_fields: Additional fields to include in log
    """
    extra = {
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
        **extra_fields,
    }
    
    # Add custom exception details if available
    if hasattr(exception, "to_dict"):
        extra.update(exception.to_dict())
    
    logger.log(level, message, exc_info=True, extra={"extra_fields": extra})


def log_operation_start(
    logger: logging.Logger,
    operation: str,
    **context: Any,
) -> None:
    """
    Log the start of an operation.
    
    Args:
        logger: Logger instance
        operation: Operation name
        **context: Context information
    """
    logger.info(
        f"Starting operation: {operation}",
        extra={"extra_fields": {"operation": operation, "status": "started", **context}},
    )


def log_operation_complete(
    logger: logging.Logger,
    operation: str,
    duration: float = None,
    **context: Any,
) -> None:
    """
    Log the completion of an operation.
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration: Operation duration in seconds
        **context: Context information
    """
    extra = {"operation": operation, "status": "completed", **context}
    
    if duration is not None:
        extra["duration_seconds"] = duration
    
    logger.info(
        f"Completed operation: {operation}",
        extra={"extra_fields": extra},
    )


def log_operation_failed(
    logger: logging.Logger,
    operation: str,
    error: Exception,
    duration: float = None,
    **context: Any,
) -> None:
    """
    Log a failed operation.
    
    Args:
        logger: Logger instance
        operation: Operation name
        error: Exception that caused the failure
        duration: Operation duration in seconds
        **context: Context information
    """
    extra = {
        "operation": operation,
        "status": "failed",
        "error_type": type(error).__name__,
        "error_message": str(error),
        **context,
    }
    
    if duration is not None:
        extra["duration_seconds"] = duration
    
    # Add custom exception details if available
    if hasattr(error, "to_dict"):
        extra.update(error.to_dict())
    
    logger.error(
        f"Operation failed: {operation}",
        exc_info=True,
        extra={"extra_fields": extra},
    )
