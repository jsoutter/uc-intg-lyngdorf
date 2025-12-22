"""
Media-player entity functions for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import EntityTypes, MediaPlayer, StatusCodes, media_player
from ucapi.media_player import Attributes, Commands, DeviceClasses
from ucapi_framework import create_entity_id

from const import LyngdorfConfig
from device import LyngdorfDevice

_LOG = logging.getLogger(__name__)

features = [
    media_player.Features.ON_OFF,
    media_player.Features.VOLUME,
    media_player.Features.VOLUME_UP_DOWN,
    media_player.Features.MUTE_TOGGLE,
    media_player.Features.MUTE,
    media_player.Features.UNMUTE,
    media_player.Features.PLAY_PAUSE,
    media_player.Features.NEXT,
    media_player.Features.PREVIOUS,
    media_player.Features.SELECT_SOURCE,
    # MP devices only
    # media_player.Features.DPAD,
    # media_player.Features.NUMPAD,
    # media_player.Features.MENU,
    # media_player.Features.INFO,
    # media_player.Features.SETTINGS,
]


class LyngdorfMediaPlayer(MediaPlayer):
    """Representation of a Lyngdorf Media Player entity."""

    def __init__(self, config_device: LyngdorfConfig, device: LyngdorfDevice):
        """Initialize the class."""
        self._device = device
        entity_id = create_entity_id(EntityTypes.MEDIA_PLAYER, config_device.identifier)

        if config_device.multichannel:
            features.append(media_player.Features.SELECT_SOUND_MODE)

        _LOG.debug("Initializing media player entity: %s", entity_id)

        super().__init__(
            entity_id,
            config_device.name,
            features,
            attributes={
                Attributes.STATE: device.state,
                Attributes.MUTED: device.receiver.muted,
                Attributes.VOLUME: device.volume_percent,
                Attributes.SOURCE: device.receiver.source,
                Attributes.SOURCE_LIST: device.receiver.sources,
                **(
                    {
                        Attributes.SOUND_MODE: device.receiver.audio_mode,
                        Attributes.SOUND_MODE_LIST: device.receiver.audio_modes,
                    }
                    if config_device.multichannel
                    else {}
                ),
            },
            device_class=DeviceClasses.RECEIVER,
            cmd_handler=self.media_player_cmd_handler,  # type: ignore
        )

    async def media_player_cmd_handler(  # noqa: C901
        self, entity: MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """
        Media-player entity command handler.

        Called by the integration-API if a command is sent to a configured media-player entity.

        :param entity: media-player entity
        :param cmd_id: command
        :param params: optional command parameters
        :return: status code of the command. StatusCodes.OK if the command succeeded.
        """
        _LOG.info("Got %s command request: %s %s", self.id, cmd_id, params if params else "")

        try:
            cmd = Commands(cmd_id)
        except ValueError:
            return StatusCodes.BAD_REQUEST

        try:
            match cmd:
                case Commands.ON:
                    await self._device.receiver.async_power_on()
                case Commands.OFF:
                    await self._device.receiver.async_power_off()
                case Commands.VOLUME:
                    volume: float = params.get("volume")  # type: ignore
                    await self._device.set_volume(volume)
                case Commands.VOLUME_UP:
                    await self._device.receiver.async_volume_up()
                case Commands.VOLUME_DOWN:
                    await self._device.receiver.async_volume_down()
                case Commands.MUTE_TOGGLE:
                    await self._device.mute_toggle()
                case Commands.MUTE:
                    await self._device.receiver.async_mute(True)
                case Commands.UNMUTE:
                    await self._device.receiver.async_mute(False)
                case Commands.PLAY_PAUSE:
                    await self._device.receiver.async_play()
                case Commands.NEXT:
                    await self._device.receiver.async_next()
                case Commands.PREVIOUS:
                    await self._device.receiver.async_previous()
                case Commands.SELECT_SOURCE:
                    source: str = params.get("source")  # type: ignore
                    await self._device.receiver.async_set_source(source)
                case Commands.SELECT_SOUND_MODE:
                    mode: str = params.get("mode")  # type: ignore
                    await self._device.receiver.async_set_audio_mode(mode)
                case _:
                    return StatusCodes.NOT_IMPLEMENTED

        except Exception as ex:
            _LOG.error("Error executing command %s: %s", cmd_id, ex)
            return StatusCodes.BAD_REQUEST

        return StatusCodes.OK
