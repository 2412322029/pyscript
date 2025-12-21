import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Dict, Any


def configure_logging() -> Dict[str, Any]:
    """Configure application logging with file rotation and structured formatting"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Log file path
    log_file = os.path.join(log_dir, "app.log")

    # Define log format
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create rotating file handler (5 files max, 5MB each)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.DEBUG)

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO, handlers=[file_handler, console_handler], force=True
    )

    # Disable unwanted loggers
    disable_loggers = [
        "uvicorn.access",  # Disable default access logs
        "uvicorn.http.httptools_impl",
        "fastapi.middleware.cors",
        "sqlalchemy.engine.Engine",
        "huey.consumer.Consumer",
    ]

    for logger_name in disable_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
        logger.propagate = False

    # Return logging configuration for FastAPI
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
            }
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": log_file,
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "default",
                "level": "INFO",
            },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "DEBUG",
            },
        },
        "loggers": {"uvicorn.access": {"level": "WARNING", "propagate": False}},
    }
