"""
Sensor entity functions for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import EntityTypes
from ucapi.sensor import Attributes, DeviceClasses, Sensor, States
from ucapi_framework import create_entity_id

from const import LyngdorfConfig, LyngdorfSensorConfig

_LOG = logging.getLogger(__name__)


class LyngdorfSensor(Sensor):
    """Representation of a Lyngdorf Sensor entity."""

    def __init__(self, config_device: LyngdorfConfig, sensor: LyngdorfSensorConfig):
        """Initialize a Lyngdorf Sensor entity."""
        self.default_value: str = sensor.default_value

        entity_id = create_entity_id(EntityTypes.SENSOR, config_device.identifier, sensor.identifier)
        attributes: dict[str, Any] = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VALUE: self.default_value,
            **({Attributes.UNIT: sensor.unit_of_measurement} if sensor.unit_of_measurement is not None else {}),
        }

        _LOG.debug("Initializing sensor entity: %s", entity_id)

        super().__init__(
            identifier=entity_id,
            name=f"{config_device.name} {sensor.name}",
            features=[],
            attributes=attributes,
            device_class=DeviceClasses.CUSTOM,
            options=sensor.options,
        )
