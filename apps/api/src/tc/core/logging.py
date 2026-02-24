import logging

from tc.core.config import settings


def configure_logging() -> None:
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))
