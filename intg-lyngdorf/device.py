"""
This module implements communication for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from asyncio import AbstractEventLoop
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from pylyngdorf.const import DeviceModel, LyngdorfQuery
from pylyngdorf.lyngdorf import Lyngdorf
from ucapi import EntityTypes
from ucapi.media_player import Attributes as MediaAttr
from ucapi.sensor import Attributes as SensorAttr
from ucapi_framework import BaseConfigManager, PersistentConnectionDevice, create_entity_id
from ucapi_framework.device import DeviceEvents

from const import SENSOR_TYPES, LyngdorfConfig, LyngdorfSensorConfig

_LOG = logging.getLogger(__name__)


class PowerState(StrEnum):
    """Power state enumeration for the device."""

    OFF = "OFF"
    ON = "ON"


class LyngdorfDevice(PersistentConnectionDevice):
    """Handles communication with a Lyngdorf over TCP."""

    def __init__(
        self,
        device_config: LyngdorfConfig,
        loop: AbstractEventLoop | None = None,
        config_manager: BaseConfigManager[LyngdorfConfig] | None = None,
    ) -> None:
        """Create instance."""
        super().__init__(  # type: ignore
            device_config,
            loop,
            config_manager=config_manager,
        )

        try:
            model = DeviceModel(device_config.model)
        except ValueError:
            model = DeviceModel.MP60

        self._receiver: Lyngdorf = Lyngdorf.create(
            device_config.address,
            device_config.port,
            device_model=model,
        )

        self._available_sensors = tuple(
            sensor
            for sensor in SENSOR_TYPES
            if not sensor.multichannel or sensor.multichannel == device_config.multichannel
        )
        self._indentifier_sensor = MappingProxyType({s.identifier: s for s in self._available_sensors})
        self._event_sensor = MappingProxyType({s.event: s for s in self._available_sensors})

    @property
    def identifier(self) -> str:
        """Return the device identifier."""
        return self._device_config.identifier

    @property
    def name(self) -> str:
        """Return the device name."""
        return self._device_config.name

    @property
    def address(self) -> str | None:
        """Return the optional device address."""
        return self.device_config.address

    @property
    def log_id(self) -> str:
        """Return a log identifier."""
        return self.device_config.identifier

    @property
    def state(self) -> PowerState | None:
        """Return the current power state."""
        return PowerState.ON if self.receiver.power else PowerState.OFF

    @property
    def attributes(self) -> dict[str, Any]:
        """Return the device attributes."""
        updated_data: dict[str, Any] = {
            MediaAttr.STATE: self.state,
            MediaAttr.MUTED: self.receiver.muted,
            MediaAttr.VOLUME: self.volume_percent,
        }

        if self.receiver.source:
            updated_data[MediaAttr.SOURCE] = self.receiver.source
        if self.receiver.sources:
            updated_data[MediaAttr.SOURCE_LIST] = self.receiver.sources
        if self.receiver.audio_mode:
            updated_data[MediaAttr.SOUND_MODE] = self.receiver.audio_mode
        if self.receiver.audio_modes:
            updated_data[MediaAttr.SOUND_MODE_LIST] = self.receiver.audio_modes

        return updated_data

    @property
    def receiver(self) -> Lyngdorf:
        """Return the device identifier."""
        return self._receiver

    @property
    def volume_percent(self) -> float:
        """Return the volume percent of the device as float."""
        return round(self.receiver.volume_percent * 100, 1) if self.receiver.volume_percent else 0.0

    @property
    def available_sensors(self) -> tuple[LyngdorfSensorConfig, ...]:
        """Configuration for available sensors."""
        return self._available_sensors

    def sensor_value(self, identifier: str) -> dict[str, Any]:
        """Get sensor value using identifier."""
        sensor = self._indentifier_sensor.get(identifier)
        return self._sensor_value(sensor) if sensor else {}

    async def establish_connection(self):
        """Establish connection."""
        await self.receiver.async_connect()

        self._update_attributes()
        self._update_sensors()
        self.receiver.set_notification_callback(self._update_entities)
        return self.receiver

    async def close_connection(self) -> None:
        """Close connection."""
        await self.receiver.async_disconnect()

    async def maintain_connection(self) -> None:
        """Maintain connection."""
        await self.receiver.wait_while_connected()

    def _update_entities(self, event: LyngdorfQuery) -> None:
        """Update entities based upon event."""
        _LOG.debug("Event %s for device id %s", event.name, self.identifier)

        if event in {
            LyngdorfQuery.POWER,
            LyngdorfQuery.VOLUME,
            LyngdorfQuery.MUTE,
            LyngdorfQuery.SOURCE,
            LyngdorfQuery.SOURCE_LIST,
            LyngdorfQuery.AUDIO_MODE,
            LyngdorfQuery.AUDIO_MODE_LIST,
        }:
            self._update_attributes()

        if event == LyngdorfQuery.POWER:
            self._update_remote()
            self._update_sensors()

        if sensor := self._event_sensor.get(event):
            self._update_sensor(sensor)

    def _update_attributes(self) -> None:
        """Update media player attributes."""
        self.events.emit(
            DeviceEvents.UPDATE,  # type: ignore
            create_entity_id(EntityTypes.MEDIA_PLAYER, self.identifier),
            self.attributes,
        )

    def _update_remote(self) -> None:
        """Update media player attributes."""
        self.events.emit(
            DeviceEvents.UPDATE,  # type: ignore
            create_entity_id(EntityTypes.REMOTE, self.identifier),
            {SensorAttr.STATE: self.state},
        )

    def _update_sensors(self) -> None:
        """Update available sensor values."""
        for sensor in self._available_sensors:
            self._update_sensor(sensor)

    def _update_sensor(self, sensor: LyngdorfSensorConfig) -> None:
        """Update sensor value."""
        self.events.emit(
            DeviceEvents.UPDATE,  # type: ignore
            create_entity_id(EntityTypes.SENSOR, self.identifier, sensor.identifier),
            self._sensor_value(sensor),
        )

    def _sensor_value(self, sensor: LyngdorfSensorConfig) -> dict[str, Any]:
        """Return value for sensor"""
        value = sensor.value_fn(self.receiver)
        update: dict[str, Any] = {
            SensorAttr.STATE: self.state,
            SensorAttr.VALUE: value if self.state == PowerState.ON and value is not None else sensor.default_value,
            **({SensorAttr.UNIT: sensor.unit_of_measurement} if sensor.unit_of_measurement is not None else {}),
        }
        return update

    # ##########
    # # Setter #
    # ##########
    async def set_volume(self, volume: float):
        """Set device volume percent."""
        await self.receiver.async_set_volume_percent(volume / 100)

    async def mute_toggle(self) -> None:
        """Mute device."""
        await self.receiver.async_mute(not self.receiver.muted)
