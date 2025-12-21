#!/usr/bin/env python3
"""
This module implements a Unfolded Circle integration driver for Lyngdorf devices.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
import os
from typing import Any

from ucapi import Entity
from ucapi.sensor import Attributes as SensorAttr
from ucapi_framework import BaseConfigManager, BaseIntegrationDriver, get_config_path

from const import LYNGDORF_SERVICE_TYPE, LyngdorfConfig
from device import LyngdorfDevice
from discover import LyngdorfDiscovery
from media_player import LyngdorfMediaPlayer, media_player
from remote import LyngdorfRemote
from sensor import LyngdorfSensor
from setup import LyngdorfSetupFlow

_LOG = logging.getLogger("driver")


class LyngdorfIntegrationDriver(BaseIntegrationDriver[LyngdorfDevice, LyngdorfConfig]):
    """Lyngdorf Integration Driver"""

    def register_available_entities(self, device_config: LyngdorfConfig, device: LyngdorfDevice) -> None:
        """Register entities based on device capabilities."""
        _LOG.info("Registering entities for Lyngdorf: %s", device.identifier)

        entities: list[Entity] = []
        entities.append(LyngdorfMediaPlayer(device_config, device))
        entities.append(LyngdorfRemote(device_config, device))

        for sensor in device.available_sensors:
            entities.append(LyngdorfSensor(device_config, sensor))

        # Register all entities with the API
        for entity in entities:
            if self.api.available_entities.contains(entity.id):
                _LOG.debug("Removing existing entity: %s", entity.id)
                self.api.available_entities.remove(entity.id)
            _LOG.debug("Adding entity: %s", entity.id)
            self.api.available_entities.add(entity)

    async def refresh_entity_state(self, entity_id: str) -> None:
        """Set initial entity state."""
        configured_entity = self.api.configured_entities.get(entity_id)
        if configured_entity is None:
            _LOG.debug("Entity %s is not configured, ignoring", entity_id)
            return

        if isinstance(configured_entity, LyngdorfRemote | LyngdorfSensor):
            device_id = self.device_from_entity_id(entity_id)
            if device_id is None:
                return

            device = self._configured_devices.get(device_id)
            if device is None:
                _LOG.warning("Device %s not found for entity %s", device_id, entity_id)
                return

            state = (
                self.map_device_state(device.state)
                if not device.is_connected or device.state
                else media_player.States.UNKNOWN
            )

            update: dict[str, Any] = {}
            if isinstance(configured_entity, LyngdorfSensor) and (
                sub_device_id := self.sub_device_from_entity_id(entity_id)
            ):
                update.update(device.sensor_value(sub_device_id))

            update.update({SensorAttr.STATE: state})
            self.api.configured_entities.update_attributes(entity_id, update)

        else:
            await super().refresh_entity_state(entity_id)


async def main():
    """Start the Remote Two/3 integration driver."""
    logging.basicConfig()

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("discover").setLevel(level)
    logging.getLogger("setup").setLevel(level)
    logging.getLogger("device").setLevel(level)
    logging.getLogger("remote").setLevel(level)
    logging.getLogger("media_player").setLevel(level)
    logging.getLogger("sensor").setLevel(level)
    logging.getLogger("pylyngdorf").setLevel(level)

    driver = LyngdorfIntegrationDriver(
        device_class=LyngdorfDevice,
        entity_classes=[],
    )

    # Initialize configuration manager with device callbacks
    driver.config_manager = BaseConfigManager(
        get_config_path(driver.api.config_dir_path),
        driver.on_device_added,
        driver.on_device_removed,
        config_class=LyngdorfConfig,
    )

    # Connect to all configured PowerView hubs
    await driver.register_all_configured_devices()

    discovery = LyngdorfDiscovery(service_type=LYNGDORF_SERVICE_TYPE, timeout=2)
    setup_handler = LyngdorfSetupFlow.create_handler(driver, discovery)  # type: ignore
    await driver.api.init("driver.json", setup_handler)

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
