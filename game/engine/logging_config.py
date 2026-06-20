from __future__ import annotations

import logging
from pathlib import Path

from game import settings


LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(log_dir: str | Path = settings.LOGS_DIR) -> None:
    log_root = Path(log_dir)
    log_root.mkdir(parents=True, exist_ok=True)
    log_path = log_root / "game.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if any(getattr(handler, "_hearthvale_handler", False) for handler in root_logger.handlers):
        return

    formatter = logging.Formatter(LOG_FORMAT)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler._hearthvale_handler = True  # type: ignore[attr-defined]
    root_logger.addHandler(file_handler)
