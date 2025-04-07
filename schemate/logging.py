"""
Manages logging configuration for schemate.
"""

import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": logging.DEBUG,
        },
    },
    "loggers": {
        "schemate": {
            "handlers": ["console"],
            "level": logging.DEBUG,
            "propagate": False,
        },
        "root": {
            "handlers": ["console"],
            "level": logging.DEBUG,
            "propagate": False,
        },
    },
    "disable_existing_loggers": True,
}


def setup_logging():
    """
    Set up logging configuration for schemate.
    """
    logging.config.dictConfig(LOGGING_CONFIG)
