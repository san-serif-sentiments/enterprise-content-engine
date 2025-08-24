from __future__ import annotations
import logging, datetime, pathlib

LOG_DIR = pathlib.Path(__file__).resolve().parent.parent / "logs"

def get_logger(name: str) -> logging.Logger:
    """Create a logger that writes to the role-specific log file."""
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_DIR / f"{datetime.date.today()}-{name}.log")
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
