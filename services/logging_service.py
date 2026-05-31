import logging
from pathlib import Path


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "daily_helper.log"


def setup_logging() -> logging.Logger:
    """
    Sets up app-wide logging.

    Logs go to:
    - the PyCharm terminal
    - Azure App Service Log Stream
    - logs/daily_helper.log locally
    """
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger("daily_helper")
    logger.setLevel(logging.INFO)

    # Avoid duplicate log lines when Streamlit reruns.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()