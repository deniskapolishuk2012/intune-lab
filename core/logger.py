import os
import logging
from datetime import datetime

# Logs directory — at project root level
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger that writes to both console and a daily log file.

    Usage:
        from core.logger import get_logger
        log = get_logger("engine")
        log.info("Starting engine")
        log.warning("Device is non-compliant")
        log.error("Failed to assign policy")

    Log files are created daily:
        logs/engine_2026-05-04.log
        logs/validate_2026-05-04.log
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # --- Format ---
    fmt = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)-8s | %(name)-12s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # --- Console handler (INFO and above) ---
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # --- File handler (DEBUG and above, daily rotation) ---
    today    = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOGS_DIR, f"{name}_{today}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
