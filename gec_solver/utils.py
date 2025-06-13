"""
Utility functions for the GEC solver package.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional


def setup_logging(
    log_level: str = "INFO", log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration for the GEC solver.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, logs to console only.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("gec_solver")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def tobits(num: int, bit_len: int) -> str:
    """
    Convert number to binary string with specified bit length.

    Args:
        num: Number to convert
        bit_len: Length of binary string

    Returns:
        Binary string representation
    """
    res = ""
    for pos in range(bit_len):
        res = str(num % 2) + res
        num //= 2
    return res


def ensure_directory(path: str) -> None:
    """
    Ensure directory exists, create if it doesn't.

    Args:
        path: Directory path to ensure
    """
    if not os.path.exists(path):
        os.makedirs(path)
        logging.getLogger("gec_solver").info(f"Created directory: {path}")


def get_timestamp() -> str:
    """
    Get current timestamp string.

    Returns:
        Timestamp string in format YYYY-MM-DD_HH-MM-SS
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def validate_sbox(sbox: List[int], bit_num: int) -> bool:
    """
    Validate S-box structure and values.

    Args:
        sbox: S-box values
        bit_num: Number of bits

    Returns:
        True if valid, False otherwise
    """
    expected_size = 2**bit_num
    if len(sbox) != expected_size:
        return False

    # Check if all values are within valid range
    max_val = expected_size - 1
    for val in sbox:
        if not (0 <= val <= max_val):
            return False

    # Check if S-box is a permutation (all values unique)
    if len(set(sbox)) != len(sbox):
        return False

    return True
