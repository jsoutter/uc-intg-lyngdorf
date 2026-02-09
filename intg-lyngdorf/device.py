"""
This module implements communication for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import base64
import io
import logging
import socket
import ssl
from asyncio import AbstractEventLoop
from collections.abc import Coroutine
from dataclasses import replace
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, TypeAlias

import aiohttp
import certifi
from PIL import Image
from pylyngdorf.const import DeviceModel, LyngdorfQuery
from pylyngdorf.lyngdorf import Lyngdorf
from pylyngdorf.music_player import MediaState
from ucapi import EntityTypes, media_player, sensor
from ucapi.media_player import Attributes as MediaAttr
from ucapi.media_player import MediaType
from ucapi.remote import Attributes as RemoteAttr
from ucapi.sensor import Attributes as SensorAttr
from ucapi_framework import (
    BaseConfigManager,
    BaseIntegrationDriver,
    EntitySource,
    PersistentConnectionDevice,
    create_entity_id,
)
from ucapi_framework.device import DeviceEvents

from const import SENSOR_TYPES, LyngdorfConfig, LyngdorfSensorConfig

_LOG = logging.getLogger(__name__)

_MEDIA_PLAYER_STATE_MAP = {
    MediaState.BUFFERING: media_player.States.BUFFERING,
    MediaState.PLAYING: media_player.States.PLAYING,
    MediaState.PAUSED: media_player.States.PAUSED,
}

_ssl_context = ssl.create_default_context(cafile=certifi.where())


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

        self._media_player_entity_id = create_entity_id(EntityTypes.MEDIA_PLAYER, self.identifier)
        self._remote_entity_id = create_entity_id(EntityTypes.REMOTE, self.identifier)
        self._available_sensors = tuple(
            replace(sensor, entity_id=create_entity_id(EntityTypes.SENSOR, self.identifier, sensor.identifier))
            for sensor in SENSOR_TYPES
            if not sensor.multichannel or sensor.multichannel == device_config.multichannel
        )
        self._sensor_events = MappingProxyType({s.event: s for s in self._available_sensors})

        self._state = media_player.States.OFF
        self._is_on: bool = False
        self._media_player_attributes: dict[str, Any] = {MediaAttr.STATE: self.state}
        self._sensor_attributes: dict[str, dict[str, Any]] = {}

        self._image_cache: str | None = None
        self._image_cache_url: str | None = None
        self._background_tasks: set[asyncio.Task[None]] = set()
        self._current_image_task: asyncio.Task[None] | None = None
        self._current_image_task_url: str | None = None

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
    def receiver(self) -> Lyngdorf:
        """Return the device identifier."""
        return self._receiver

    @property
    def media_player_attributes(self) -> dict[str, Any]:
        """Return the media player attributes."""
        return self._media_player_attributes

    @property
    def remote_attributes(self) -> dict[str, Any]:
        """Return the remote attributes."""
        return {RemoteAttr.STATE: self.state}

    @property
    def available_sensors(self) -> tuple[LyngdorfSensorConfig, ...]:
        """Configuration for available sensors."""
        return self._available_sensors

    async def establish_connection(self):
        """Establish connection."""
        await self.receiver.async_connect()
        self._receiver.set_notification_callback(self._update_entities)

        self._update_state()
        self._update_media_player()
        self._update_remote()
        self._update_sensors()
        return self.receiver

    async def close_connection(self) -> None:
        """Close connection."""
        await self.receiver.async_disconnect()

        # Cancel all tasks tracked background tasks
        for task in list(self._background_tasks):
            task.cancel()
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()

    async def maintain_connection(self) -> None:
        """Maintain connection."""
        await self.receiver.wait_while_connected()

    def get_device_attributes(self, entity_id: str) -> dict[str, Any]:
        """Return the attributes for the given entity ID."""
        match entity_id:
            case self._media_player_entity_id:
                return self.media_player_attributes
            case self._remote_entity_id:
                return self.remote_attributes
            case _:
                return self._sensor_attributes.get(entity_id, {})

    def _update_entities(self, event: LyngdorfQuery) -> None:
        """Update entities based upon event."""
        _LOG.debug("Event %s for device id %s", event.name, self.identifier)

        if event in (LyngdorfQuery.POWER, LyngdorfQuery.MEDIA_DATA):
            self._update_state()

        match event:
            case LyngdorfQuery.POWER | LyngdorfQuery.MEDIA_DATA:
                self._update_media_player()
                self._update_remote()
                if event == LyngdorfQuery.POWER:
                    self._update_sensors()
            case (
                LyngdorfQuery.VOLUME
                | LyngdorfQuery.MUTE
                | LyngdorfQuery.SOURCE
                | LyngdorfQuery.SOURCE_LIST
                | LyngdorfQuery.AUDIO_MODE
                | LyngdorfQuery.AUDIO_MODE_LIST
            ):
                self._update_media_player()
            case _:
                pass

        if sensor := self._sensor_events.get(event):
            self._update_sensor(sensor)

    def _update_state(self) -> None:
        """Update state attributes."""
        if not self.receiver.power:
            self._state = media_player.States.OFF
        else:
            self._state = _MEDIA_PLAYER_STATE_MAP.get(self._receiver.media_data.state, media_player.States.ON)

        self._is_on = self._state is not media_player.States.OFF

    def _update_media_player(self) -> None:
        """Update media player attributes."""
        receiver = self.receiver
        now_iso = datetime.now(tz=UTC).isoformat()
        is_not_stopped = receiver.media_data.state != MediaState.STOPPED

        updated_data: dict[str, Any] = {
            MediaAttr.STATE: self.state,
            MediaAttr.MUTED: receiver.muted,
            MediaAttr.VOLUME: round(receiver.volume_level * 100, 1) if receiver.volume_level else 0.0,
            MediaAttr.SOURCE: receiver.source or "",
            MediaAttr.SOURCE_LIST: receiver.sources,
            MediaAttr.MEDIA_DURATION: receiver.media_data.duration,
            MediaAttr.MEDIA_POSITION: receiver.media_data.position,
            MediaAttr.MEDIA_POSITION_UPDATED_AT: now_iso if is_not_stopped else None,
            MediaAttr.MEDIA_TITLE: receiver.media_data.title or "",
            MediaAttr.MEDIA_ARTIST: receiver.media_data.artist or "",
            MediaAttr.MEDIA_ALBUM: receiver.media_data.album or "",
            MediaAttr.MEDIA_TYPE: MediaType.MUSIC if is_not_stopped else "",
        }

        if self.device_config.multichannel:
            updated_data.update(
                {
                    MediaAttr.SOUND_MODE: receiver.audio_mode or "",
                    MediaAttr.SOUND_MODE_LIST: receiver.audio_modes,
                }
            )

        # Handle image caching
        new_image_url = receiver.media_data.image_url
        if new_image_url:
            if new_image_url != self._image_cache_url:
                self._fetch_image(new_image_url, self._media_player_entity_id, 0.5)
            elif not self._media_player_attributes.get(MediaAttr.MEDIA_IMAGE_URL) and self._image_cache:
                updated_data[MediaAttr.MEDIA_IMAGE_URL] = self._image_cache
        else:
            updated_data[MediaAttr.MEDIA_IMAGE_URL] = None
            self._image_cache = self._image_cache_url = None

        self._media_player_attributes.update(updated_data)
        self.events.emit(DeviceEvents.UPDATE, self._media_player_entity_id, self._media_player_attributes)

    def _update_remote(self) -> None:
        """Update media player attributes."""
        self.events.emit(DeviceEvents.UPDATE, self._remote_entity_id, self.remote_attributes)

    def _update_sensors(self) -> None:
        """Update available sensor values."""
        for sensor_config in self._available_sensors:
            self._update_sensor(sensor_config)

    def _update_sensor(self, sensor_config: LyngdorfSensorConfig) -> None:
        """Update sensor value."""
        entity_id = sensor_config.entity_id
        sensor_value = (sensor_config.value_fn(self.receiver) if self._is_on else None) or sensor_config.default

        attrs = self._sensor_attributes.setdefault(entity_id, {})
        attrs.update(
            {
                SensorAttr.STATE: sensor.States.ON if self._is_on else sensor.States.UNKNOWN,
                SensorAttr.VALUE: sensor_value,
                SensorAttr.UNIT: sensor_config.unit,
            }
        )

        if self.driver and self.driver.get_entity_by_id(entity_id, EntitySource.CONFIGURED):
            self.events.emit(DeviceEvents.UPDATE, entity_id, attrs)

    def _create_task(self, coro: Coroutine[None, None, None], delay: float = 0) -> asyncio.Task[None]:
        """Create a background task and track it."""

        async def delayed_coro():
            if delay > 0:
                await asyncio.sleep(delay)
            await coro

        task: asyncio.Task[None] = self._loop.create_task(delayed_coro())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return task

    def _fetch_image(self, url: str, identifier: str, delay: float = 0) -> None:
        """Fetch image ensuring only one active task."""
        _LOG.debug("Fetch image requested: %s", url)
        current_task = self._current_image_task
        current_url = self._current_image_task_url

        if current_task and not current_task.done():
            if current_url == url:
                _LOG.debug("Image fetch already in progess.")
                return
            # Cancel ongoing fetch for a different URL
            current_task.cancel()

        self._current_image_task_url = url
        self._current_image_task = self._create_task(self._fetch_and_update_image(url, identifier), delay)

    async def _fetch_and_update_image(self, url: str, identifier: str):
        """Fetch image asynchronously and emit update event."""
        try:
            image_data = await self._store_image_as_base64(url, 400)
            if image_data:
                updated_data: dict[str, Any] = {MediaAttr.MEDIA_IMAGE_URL: image_data}
                self._media_player_attributes.update(updated_data)
                self.events.emit(DeviceEvents.UPDATE, identifier, updated_data)
        except Exception as ex:
            _LOG.error("Failed to fetch and update image: %s", ex)

    async def _store_image_as_base64(self, url: str, max_size: int) -> str | None:
        """Retrieve and store image as base64 data."""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            connector = aiohttp.TCPConnector(family=socket.AF_INET, ssl=_ssl_context)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_bytes = await response.read()
                        image = await asyncio.to_thread(lambda: Image.open(io.BytesIO(image_bytes)).convert("RGBA"))

                        width, height = image.size
                        if max_size >= max(width, height):
                            new_width, new_height = width, height
                        elif width > height:
                            new_width = max_size
                            new_height = int(height * (max_size / width))
                        else:
                            new_height = max_size
                            new_width = int(width * (max_size / height))

                        if (new_width, new_height) != (width, height):
                            new_size: tuple[int, int] = (new_width, new_height)
                            image = image.resize(new_size, Image.Resampling.LANCZOS)  # type: ignore[reportUnknownMemberType]

                        buffer = io.BytesIO()
                        image.save(buffer, format="PNG")
                        image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

                        self._image_cache = f"data:image/png;base64,{image_b64}"
                        self._image_cache_url = url

        except Exception as ex:
            _LOG.error("Failed to fetch image from %s: %s", url, ex)
            return ""
        return self._image_cache

    # ##########
    # # Setter #
    # ##########
    async def set_volume(self, volume: float):
        """Set device volume percent."""
        await self.receiver.async_set_volume_level(volume / 100)

    async def mute_toggle(self) -> None:
        """Mute device."""
        await self.receiver.async_mute(not self.receiver.muted)
