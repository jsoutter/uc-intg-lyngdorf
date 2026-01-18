"""
This module implements communication for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from asyncio import AbstractEventLoop
from dataclasses import replace
from types import MappingProxyType
from typing import Any, TypeAlias

from pylyngdorf.const import DeviceModel, LyngdorfQuery
from pylyngdorf.lyngdorf import Lyngdorf
from ucapi import EntityTypes, media_player
from ucapi.media_player import Attributes as MediaAttr
from ucapi.remote import Attributes as RemoteAttr
from ucapi.sensor import Attributes as SensorAttr
from ucapi_framework import (
    BaseConfigManager,
    BaseIntegrationDriver,
    PersistentConnectionDevice,
    create_entity_id,
)
from ucapi_framework.device import DeviceEvents

from const import SENSOR_TYPES, LyngdorfConfig, LyngdorfSensorConfig

_LOG = logging.getLogger(__name__)

LyngdorfDeviceType: TypeAlias = "LyngdorfDevice"


class LyngdorfDevice(PersistentConnectionDevice):
    """Handles communication with a Lyngdorf over TCP."""

    def __init__(
        self,
        device_config: LyngdorfConfig,
        loop: AbstractEventLoop | None = None,
        config_manager: BaseConfigManager[LyngdorfConfig] | None = None,
        driver: BaseIntegrationDriver[LyngdorfDeviceType, LyngdorfConfig] | None = None,
    ) -> None:
        """Create instance."""
        super().__init__(  # type: ignore
            device_config,
            loop,
            config_manager=config_manager,
            driver=driver,
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
        self._receiver.set_notification_callback(self._update_entities)

        self._media_player_entity_id = create_entity_id(EntityTypes.MEDIA_PLAYER, self.identifier)
        self._remote_entity_id = create_entity_id(EntityTypes.REMOTE, self.identifier)
        self._available_sensors = tuple(
            replace(sensor, entity_id=create_entity_id(EntityTypes.SENSOR, self.identifier, sensor.identifier))
            for sensor in SENSOR_TYPES
            if not sensor.multichannel or sensor.multichannel == device_config.multichannel
        )
        self._sensor_events = MappingProxyType({s.event: s for s in self._available_sensors})
        self._sensor_attributes: dict[str, dict[str, Any]] = {}

    @property
    def identifier(self) -> str:
        """Return the device identifier."""
        return self.device_config.identifier

    @property
    def name(self) -> str:
        """Return the device name."""
        return self.device_config.name

    @property
    def address(self) -> str | None:
        """Return the optional device address."""
        return self.device_config.address

    @property
    def log_id(self) -> str:
        """Return a log identifier."""
        return self.device_config.identifier

    @property
    def state(self) -> media_player.States | None:
        """Return the current power state."""
        return media_player.States.ON if self.receiver.power else media_player.States.OFF

    @property
    def available_sensors(self) -> tuple[LyngdorfSensorConfig, ...]:
        """Configuration for available sensors."""
        return self._available_sensors

    @property
    def receiver(self) -> Lyngdorf:
        """Return the device identifier."""
        return self._receiver

    @property
    def volume_level(self) -> float:
        """Return the volume percent of the device as float."""
        return round(self.receiver.volume_level * 100, 1) if self.receiver.volume_level else 0.0

    @property
    def _media_player_attributes(self) -> dict[str, Any]:
        """Return the media player attributes."""
        updated_data: dict[str, Any] = {
            MediaAttr.STATE: self.state,
            MediaAttr.MUTED: self.receiver.muted,
            MediaAttr.VOLUME: self.volume_level,
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
    def _remote_attributes(self) -> dict[str, Any]:
        """Return the remote attributes."""
        return {RemoteAttr.STATE: self.state}

    async def establish_connection(self):
        """Establish connection."""
        await self.receiver.async_connect()

        self._update_media_player()
        self._update_remote()
        self._update_sensors()
        return self.receiver

    async def close_connection(self) -> None:
        """Close connection."""
        await self.receiver.async_disconnect()

    async def maintain_connection(self) -> None:
        """Maintain connection."""
        await self.receiver.wait_while_connected()

    def get_device_attributes(self, entity_id: str) -> dict[str, Any]:
        """Get the device attributes for the given entity ID."""
        if EntityTypes.MEDIA_PLAYER in entity_id:
            return self._media_player_attributes
        elif EntityTypes.REMOTE in entity_id:
            return self._remote_attributes
        elif entity_id in self._sensor_attributes:
            return self._sensor_attributes[entity_id]

        return {}

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
            self._update_media_player()

        if event == LyngdorfQuery.POWER:
            self._update_remote()
            self._update_sensors()

        if sensor := self._sensor_events.get(event):
            self._update_sensor(sensor)

    def _update_media_player(self) -> None:
        """Update media player attributes."""
        self.events.emit(DeviceEvents.UPDATE, self._media_player_entity_id, self._media_player_attributes)

    def _update_remote(self) -> None:
        """Update media player attributes."""
        self.events.emit(DeviceEvents.UPDATE, self._remote_entity_id, self._remote_attributes)

    def _update_sensors(self) -> None:
        """Update available sensor values."""
        for sensor_config in self._available_sensors:
            self._update_sensor(sensor_config)

    def _update_sensor(self, sensor_config: LyngdorfSensorConfig) -> None:
        """Update sensor value."""
        entity_id = sensor_config.entity_id
        self._sensor_attributes[entity_id] = self._get_sensor_attributes(sensor_config)
        self.events.emit(DeviceEvents.UPDATE, entity_id, self._sensor_attributes[entity_id])

    def _get_sensor_attributes(self, sensor_config: LyngdorfSensorConfig) -> dict[str, Any]:
        """Return value for sensor"""
        value = sensor_config.value_fn(self.receiver)
        update: dict[str, Any] = {
            SensorAttr.STATE: self.state,
            SensorAttr.VALUE: value
            if self.state == media_player.States.ON and value is not None
            else sensor_config.default,
            **({SensorAttr.UNIT: sensor_config.unit} if sensor_config.unit is not None else {}),
        }
        return update

    # ##########
    # # Setter #
    # ##########
    async def set_volume(self, volume: float):
        """Set device volume percent."""
        await self.receiver.async_set_volume_level(volume / 100)

    async def mute_toggle(self) -> None:
        """Mute device."""
        await self.receiver.async_mute(not self.receiver.muted)
