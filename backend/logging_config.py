"""
CaptionFoundry Logging Configuration
Creates timestamped log files for each application session.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Session timestamp - set once at import time
SESSION_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
SESSION_START = datetime.now()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = DATA_DIR / "logs"


def setup_logging(level: str = "DEBUG") -> Path:
    """
    Configure logging for the current session.
    
    Creates a timestamped log file in data/logs/ and configures
    all loggers to output to both console and file.
    
    Returns:
        Path to the created log file
    """
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Log file path with session timestamp
    log_file = LOGS_DIR / f"captionfoundry_{SESSION_TIMESTAMP}.log"
    
    # Convert level string to logging constant
    log_level = getattr(logging, level.upper(), logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-30s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler - captures everything
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Always capture debug to file
    file_handler.setFormatter(file_formatter)
    
    # Console handler - respects configured level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything, handlers filter
    
    # Remove any existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add our handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    
    # Log session start
    logger = logging.getLogger("captionfoundry.startup")
    logger.info("=" * 70)
    logger.info(f"CaptionFoundry Session Started")
    logger.info(f"  Timestamp: {SESSION_START.isoformat()}")
    logger.info(f"  Log File:  {log_file}")
    logger.info(f"  Log Level: {level.upper()} (console), DEBUG (file)")
    logger.info("=" * 70)
    
    return log_file


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    Convenience wrapper for logging.getLogger().
    """
    return logging.getLogger(name)


def log_request(logger: logging.Logger, method: str, path: str, body: dict = None):
    """Log an API request with optional body."""
    if body:
        logger.debug(f"REQUEST: {method} {path} | Body: {body}")
    else:
        logger.debug(f"REQUEST: {method} {path}")


def log_response(logger: logging.Logger, method: str, path: str, status: int, duration_ms: float = None):
    """Log an API response with status and optional duration."""
    duration_str = f" | {duration_ms:.1f}ms" if duration_ms else ""
    logger.debug(f"RESPONSE: {method} {path} | Status: {status}{duration_str}")


def log_error(logger: logging.Logger, error: Exception, context: str = None):
    """Log an error with optional context and full traceback."""
    context_str = f" [{context}]" if context else ""
    logger.error(f"ERROR{context_str}: {type(error).__name__}: {error}", exc_info=True)
