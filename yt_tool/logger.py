"""Configure application-wide logging to file and console."""

import logging
from pathlib import Path

from .config import LOG_FILE, LOG_LEVEL


def setup_logging() -> None:
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    file_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    fmt = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # File handler: respects configured log level
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(file_level)
    fh.setFormatter(logging.Formatter(fmt))
    root.addHandler(fh)

    # Console handler: warnings and above only (avoids cluttering print output)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter(fmt))
    root.addHandler(ch)
