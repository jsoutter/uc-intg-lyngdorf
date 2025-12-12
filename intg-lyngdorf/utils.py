"""
Utility functions for logging setup and command validation in the Lyngdorf integration.

Includes:
- `setup_logger()`: Dynamically sets logging levels for UC API and related modules based on the
  `UC_LOG_LEVEL` environment variable.

These utilities support development and runtime diagnostics in UC API-based Lyngdorf integrations.
"""

import logging
import os


def setup_logger():
    """Get logger from all modules"""

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()

    logging.getLogger("ucapi.api").setLevel(level)
    logging.getLogger("ucapi.entities").setLevel(level)
    logging.getLogger("ucapi.entity").setLevel(level)
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("config").setLevel(level)
    logging.getLogger("discover").setLevel(level)
    logging.getLogger("setup_flow").setLevel(level)
    logging.getLogger("device").setLevel(level)
    logging.getLogger("remote").setLevel(level)
    logging.getLogger("media_player").setLevel(level)
    logging.getLogger("pylyngdorf").setLevel(level)
