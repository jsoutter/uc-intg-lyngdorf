"""
Media-player entity functions for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any, Final, cast

from ucapi import EntityTypes, MediaPlayer, StatusCodes, media_player
from ucapi.media_player import Attributes, DeviceClasses
from ucapi_framework import create_entity_id

from const import MEDIA_PLAYER_COMMANDS_MAP, LyngdorfConfig
from device import LyngdorfDevice

_LOG = logging.getLogger(__name__)

FEATURES: Final[tuple[media_player.Features, ...]] = (
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
)

MULTICHANNEL_FEATURES: Final[tuple[media_player.Features, ...]] = (
    media_player.Features.SELECT_SOUND_MODE,
    media_player.Features.DPAD,
    media_player.Features.NUMPAD,
    media_player.Features.MENU,
    media_player.Features.INFO,
    media_player.Features.SETTINGS,
)


class LyngdorfMediaPlayer(MediaPlayer):
    """Representation of a Lyngdorf Media Player entity."""

    def __init__(self, config_device: LyngdorfConfig, device: LyngdorfDevice):
        """Initialize the class."""
        self._device: LyngdorfDevice = device
        entity_id = create_entity_id(EntityTypes.MEDIA_PLAYER, config_device.identifier)

        features = cast(list[media_player.Features], list(FEATURES))
        if config_device.multichannel:
            features.extend(MULTICHANNEL_FEATURES)

        _LOG.debug("Initializing media player entity: %s", entity_id)

        super().__init__(
            entity_id,
            config_device.name,
            features,
            attributes={
                Attributes.STATE: device.state,
                Attributes.MUTED: device.receiver.muted,
                Attributes.VOLUME: device.volume_level,
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
            cmd_handler=self.cmd_handler,
        )

    async def cmd_handler(  # noqa: C901
        self, entity: MediaPlayer, cmd_id: str, params: dict[str, Any] | None, websocket: Any
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
            cmd = media_player.Commands(cmd_id)
        except ValueError:
            return StatusCodes.BAD_REQUEST

        try:
            match cmd:
                case media_player.Commands.ON:
                    await self._device.receiver.async_power_on()
                case media_player.Commands.OFF:
                    await self._device.receiver.async_power_off()
                case media_player.Commands.VOLUME:
                    volume: float = params.get("volume")  # type: ignore
                    await self._device.set_volume(volume)
                case media_player.Commands.VOLUME_UP:
                    await self._device.receiver.async_volume_up()
                case media_player.Commands.VOLUME_DOWN:
                    await self._device.receiver.async_volume_down()
                case media_player.Commands.MUTE_TOGGLE:
                    await self._device.mute_toggle()
                case media_player.Commands.MUTE:
                    await self._device.receiver.async_mute(True)
                case media_player.Commands.UNMUTE:
                    await self._device.receiver.async_mute(False)
                case media_player.Commands.PLAY_PAUSE:
                    await self._device.receiver.async_play()
                case media_player.Commands.NEXT:
                    await self._device.receiver.async_next()
                case media_player.Commands.PREVIOUS:
                    await self._device.receiver.async_previous()
                case media_player.Commands.SELECT_SOURCE:
                    source: str = params.get("source")  # type: ignore
                    await self._device.receiver.async_set_source(source)
                case media_player.Commands.SELECT_SOUND_MODE:
                    mode: str = params.get("mode")  # type: ignore
                    await self._device.receiver.async_set_audio_mode(mode)
                case _:
                    if mapped_cmd := MEDIA_PLAYER_COMMANDS_MAP.get(cmd_id):
                        await self._device.receiver.async_send_command(mapped_cmd)
                    else:
                        return StatusCodes.NOT_IMPLEMENTED

        except Exception as ex:
            _LOG.error("Error executing command %s: %s", cmd_id, ex)
            return StatusCodes.BAD_REQUEST

        return StatusCodes.OK
