"""Central logging setup.

Writes to logs/pipeline_YYYYMMDD.log and to the console, using the
timestamp format mm/dd/yy HH:MM:SS. Import get_logger() everywhere instead
of using print().
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime

import config

DATE_FORMAT = "%m/%d/%y %H:%M:%S"
LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(message)s"


def get_logger(name: str = "onboarding") -> logging.Logger:
    """Return a configured logger (file + console). Safe to call repeatedly."""
    logger = logging.getLogger(name)
    if logger.handlers:  # already configured
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    log_file = config.LOGS_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger
