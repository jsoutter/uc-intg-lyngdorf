"""Provides connection utilities for communicating with a Lyngdorf device."""

import asyncio
import logging
from asyncio import AbstractEventLoop, Task
from enum import IntEnum
from typing import Any

from pyee.asyncio import AsyncIOEventEmitter
from pylyngdorf.const import DeviceModel, LyngdorfQueries
from pylyngdorf.lyngdorf import Lyngdorf
from ucapi.media_player import Attributes as MediaAttr
from ucapi.sensor import Attributes as SensorAttr

from const import EntityPrefix, SensorEntityPrefix

_LOG = logging.getLogger(__name__)


class Events(IntEnum):
    """Internal driver events."""

    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTED = 2
    ERROR = 3
    UPDATE = 4


class States(IntEnum):
    """State of a connected device."""

    UNKNOWN = 0
    UNAVAILABLE = 1
    OFF = 2
    ON = 3


class LyngdorfDevice:
    """Handles communication with a Lyngdorf over TCP."""

    def __init__(
        self,
        host: str,
        port: int,
        model: DeviceModel,
        device_id: str | None = None,
        loop: AbstractEventLoop | None = None,
    ):
        # Identity and connection config
        self.device_id = device_id or "unknown"
        self.host = host
        self.port = port
        self.model = model
        self._device: Lyngdorf

        # Event loop and internal connection state
        self._event_loop = loop or asyncio.get_running_loop()
        self.events = AsyncIOEventEmitter(self._event_loop)

        self._reconnect_task: Task | None = None
        self._connected: bool = False
        self._disconnecting: bool = False
        self._is_alive: bool = False
        self._attr_state = States.OFF

        # Add properties for lists
        # sources, sounds modes, voicings, focus positions

    def __repr__(self):
        return f"<LyngdorfDevice id='{self.device_id}' at {self.host}:{self.port}>"

    def _callback(self, event: LyngdorfQueries):
        """"""
        match event:
            case LyngdorfQueries.POWER:
                # Derive value
                self._attr_state = States.ON
                self._emit_update(EntityPrefix.MEDIA_PLAYER, MediaAttr.STATE, self._attr_state)
                self._emit_update(EntityPrefix.REMOTE, MediaAttr.STATE, self._attr_state)

            case LyngdorfQueries.VOLUME:
                self._emit_update(EntityPrefix.MEDIA_PLAYER, MediaAttr.VOLUME, self._device.volume_percent)
                self._emit_update(SensorEntityPrefix.VOLUME, SensorAttr.VALUE, self._device.volume)

            case LyngdorfQueries.MUTE:
                self._emit_update(EntityPrefix.MEDIA_PLAYER, MediaAttr.MUTED, self._device.muted)

            case LyngdorfQueries.SOURCE_LIST:
                self._emit_update(EntityPrefix.MEDIA_PLAYER, MediaAttr.SOUND_MODE_LIST, self._device.sources)

            case LyngdorfQueries.SOURCE:
                self._emit_update(EntityPrefix.MEDIA_PLAYER, MediaAttr.SOURCE, self._device.source)

            case LyngdorfQueries.STREAM_TYPE:
                self._emit_update(SensorEntityPrefix.STREAM_TYPE, SensorAttr.VALUE, self._device.stream_type)

            case LyngdorfQueries.VOICING:
                self._emit_update(SensorEntityPrefix.VOICING, SensorAttr.VALUE, self._device.voicing)

            case LyngdorfQueries.FOCUS_POSITION:
                self._emit_update(SensorEntityPrefix.FOCUS_POSITION, SensorAttr.VALUE, self._device.focus_position)

            case LyngdorfQueries.AUDIO_MODE_LIST:
                self._emit_update(EntityPrefix.MEDIA_PLAYER, MediaAttr.SOUND_MODE_LIST, self._device.audio_modes)

            case LyngdorfQueries.AUDIO_MODE:
                self._emit_update(EntityPrefix.MEDIA_PLAYER, MediaAttr.SOUND_MODE, self._device.audio_mode)

            case LyngdorfQueries.AUDIO_INPUT:
                self._emit_update(SensorEntityPrefix.AUDIO_INPUT, SensorAttr.VALUE, self._device.audio_input)

            case LyngdorfQueries.AUDIO_TYPE:
                self._emit_update(SensorEntityPrefix.AUDIO_TYPE, SensorAttr.VALUE, self._device.audio_type)

            case LyngdorfQueries.VIDEO_INPUT:
                self._emit_update(SensorEntityPrefix.VIDEO_INPUT, SensorAttr.VALUE, self._device.video_input)

            case LyngdorfQueries.VIDEO_TYPE:
                self._emit_update(SensorEntityPrefix.VIDEO_TYPE, SensorAttr.VALUE, self._device.video_type)

            case LyngdorfQueries.VIDEO_OUTPUT:
                self._emit_update(SensorEntityPrefix.VIDEO_OUTPUT, SensorAttr.VALUE, self._device.video_output)

            case LyngdorfQueries.LIPSYNC:
                self._emit_update(SensorEntityPrefix.LIPSYNC, SensorAttr.VALUE, self._device.lipsync)

            case LyngdorfQueries.TRIM_BASS:
                self._emit_update(SensorEntityPrefix.BASS_TRIM, SensorAttr.VALUE, self._device.bass_trim)

            case LyngdorfQueries.TRIM_TREBLE:
                self._emit_update(SensorEntityPrefix.TREBLE_TRIM, SensorAttr.VALUE, self._device.treble_trim)

            case LyngdorfQueries.TRIM_CENTER:
                self._emit_update(SensorEntityPrefix.CENTER_TRIM, SensorAttr.VALUE, self._device.center_trim)

            case LyngdorfQueries.TRIM_HEIGHTS:
                self._emit_update(SensorEntityPrefix.HEIGHTS_TRIM, SensorAttr.VALUE, self._device.heights_trim)

            case LyngdorfQueries.TRIM_LFE:
                self._emit_update(SensorEntityPrefix.LFE_TRIM, SensorAttr.VALUE, self._device.lfe_trim)

            case LyngdorfQueries.TRIM_SURROUNDS:
                self._emit_update(SensorEntityPrefix.SURROUNDS_TRIM, SensorAttr.VALUE, self._device.surrounds_trim)

            case _:
                pass

    def _emit_update(self, prefix: str, attr: str, value: Any) -> None:
        """"""
        entity_id = f"{prefix}.{self.device_id}"
        self.events.emit(Events.UPDATE.name, entity_id, {attr: value})
