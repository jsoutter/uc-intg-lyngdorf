"""
Sensor entity functions.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi.sensor import Attributes, DeviceClasses, Options, Sensor, States

from config import LyngdorfDeviceConfig

_LOG = logging.getLogger(__name__)


class LyngdorfSensor(Sensor):
    """Representation of a Lyngdorf Sensor entity."""

    def __init__(self, config_device: LyngdorfDeviceConfig, sensor: str):
        """Initialize a Lyngdorf Sensor entity."""
        entity_id = f"{sensor}.{config_device.identifier}"
        name = config_device.model + " " + sensor.replace("_", " ").title()

        attributes: dict[str, Any] = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VALUE: "unknown",
            Attributes.UNIT: "unknown",
        }
        options: dict[str, Any] = {Options.DECIMALS: 1}

        super().__init__(
            identifier=entity_id,
            name=name,
            features=[],
            attributes=attributes,
            device_class=DeviceClasses.CUSTOM,
            options=options,
        )

        _LOG.debug("Lyngdorf Sensor init %s : %s", entity_id, attributes)

    def filter_changed_attributes(self, update: dict[str, Any]) -> dict[Attributes, Any]:
        """
        Filter the given attributes and return only the changed values.

        :param update: dictionary with attributes.
        :return: filtered entity attributes containing changed attributes only.
        """

        attributes: dict[Attributes, Any] = {}

        for key in (Attributes.STATE, Attributes.VALUE):
            if key in update and key in self.attributes:
                if update[key] != self.attributes[key]:
                    attributes[key] = update[key]

        if Attributes.STATE in attributes:
            if attributes[Attributes.STATE] == States.UNKNOWN:
                attributes[Attributes.VALUE] = "none"

        if attributes:
            _LOG.debug("Lyngdorf Sensor update attributes %s -> %s", update, attributes)

        return attributes
