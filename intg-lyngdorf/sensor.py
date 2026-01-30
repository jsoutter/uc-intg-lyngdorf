"""
Sensor entity functions for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import EntityTypes, Sensor
from ucapi.sensor import Attributes, DeviceClasses, States
from ucapi_framework import create_entity_id
from ucapi_framework.entity import Entity as FrameworkEntity

from const import LyngdorfConfig, LyngdorfSensorConfig
from device import LyngdorfDevice

_LOG = logging.getLogger(__name__)


class LyngdorfSensor(Sensor, FrameworkEntity):
    """Representation of a Lyngdorf Sensor entity."""

    def __init__(self, device_config: LyngdorfConfig, device: LyngdorfDevice, sensor_config: LyngdorfSensorConfig):
        """Initialize a Lyngdorf Sensor entity."""
        self._device = device
        self._entity_id = create_entity_id(EntityTypes.SENSOR, device_config.identifier, sensor_config.identifier)

        attributes: dict[str, Any] = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VALUE: sensor_config.default,
            Attributes.UNIT: sensor_config.unit,
        }

        _LOG.debug("Initializing sensor entity: %s", self._entity_id)

        super().__init__(
            identifier=self._entity_id,
            name=f"{device_config.name} {sensor_config.name}",
            features=[],
            attributes=attributes,
            device_class=DeviceClasses.CUSTOM,
            options=sensor_config.options,
        )
