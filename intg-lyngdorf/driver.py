#!/usr/bin/env python3
"""
This module implements a Unfolded Circle integration driver for Lyngdorf devices.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
import os

from ucapi_framework import BaseConfigManager, BaseIntegrationDriver, get_config_path

from const import LYNGDORF_SERVICE_TYPE, LyngdorfConfig
from device import LyngdorfDevice
from discover import LyngdorfDiscovery
from media_player import LyngdorfMediaPlayer
from remote import LyngdorfRemote
from sensor import LyngdorfSensor
from setup import LyngdorfSetupFlow

_LOG = logging.getLogger("driver")


async def main():
    """Start the Remote Two/3 integration driver."""
    logging.basicConfig()

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("discover").setLevel(level)
    logging.getLogger("setup").setLevel(level)
    logging.getLogger("device").setLevel(level)
    logging.getLogger("media_player").setLevel(level)
    logging.getLogger("remote").setLevel(level)
    logging.getLogger("sensor").setLevel(level)
    logging.getLogger("pylyngdorf").setLevel(level)

    driver = BaseIntegrationDriver[LyngdorfDevice, LyngdorfConfig](
        device_class=LyngdorfDevice,
        entity_classes=[
            LyngdorfMediaPlayer,
            LyngdorfRemote,
            lambda cfg, dev: [LyngdorfSensor(cfg, dev, sensor_config) for sensor_config in dev.available_sensors],
        ],
    )

    driver.config_manager = BaseConfigManager(
        get_config_path(driver.api.config_dir_path),
        driver.on_device_added,
        driver.on_device_removed,
        config_class=LyngdorfConfig,
    )

    await driver.register_all_configured_devices()

    discovery = LyngdorfDiscovery(service_type=LYNGDORF_SERVICE_TYPE, timeout=5)
    setup_handler = LyngdorfSetupFlow.create_handler(driver, discovery)  # type: ignore

    await driver.api.init("driver.json", setup_handler)

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
