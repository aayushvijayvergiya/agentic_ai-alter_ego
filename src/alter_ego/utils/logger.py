"""Logging configuration for the Alter Ego application."""

import logging
import os
import sys


def setup_logger(name: str = "alter_ego") -> logging.Logger:
    """Set up and return a logger instance."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if the logger is already set up
    if logger.handlers:
        return logger
        
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    
    logger.setLevel(log_level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# Default logger instance
logger = setup_logger()
