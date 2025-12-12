"""
Media-player entity functions.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from pylyngdorf.lyngdorf import Lyngdorf
from ucapi import EntityTypes, MediaPlayer, StatusCodes
from ucapi.media_player import Attributes, Commands, DeviceClasses, States

from config import LyngdorfDeviceConfig, create_entity_id
from const import MediaPlayerDef, SimpleCommands

_LOG = logging.getLogger(__name__)


class LyngdorfMediaPlayer(MediaPlayer):
    """Representation of a Lyngdorf Media Player entity."""

    def __init__(self, config_device: LyngdorfDeviceConfig, device: Lyngdorf):
        """Initialize the class."""
        self._device = device
        entity_id = create_entity_id(config_device.identifier, EntityTypes.MEDIA_PLAYER)
        features = MediaPlayerDef.features
        attributes = MediaPlayerDef.attributes
        self.simple_commands = [*SimpleCommands]

        # options: dict[str, Any] = {Options.SIMPLE_COMMANDS: self.simple_commands}
        super().__init__(
            entity_id,
            f"{config_device.model} Media Player",
            features,
            attributes,
            device_class=DeviceClasses.RECEIVER,
            # options=options,
        )

        _LOG.debug("LyngdorfMediaPlayer init %s : %s", entity_id, attributes)

    async def command(self, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """
        Media-player entity command handler.

        Called by the integration-API if a command is sent to a configured media-player entity.

        :param cmd_id: command
        :param params: optional command parameters
        :return: status code of the command request
        """
        _LOG.info("Got %s command request: %s %s", self.id, cmd_id, params)

        try:
            cmd = Commands(cmd_id)
        except ValueError:
            return StatusCodes.BAD_REQUEST

        match cmd:
            case Commands.ON:
                # res = await self._device.power_on()
                res = StatusCodes.OK
            case Commands.OFF:
                # res = await self._device.power_off()
                res = StatusCodes.OK
            # case Commands.PLAY_PAUSE:
            #     res = StatusCodes.OK
            # case Commands.NEXT:
            #     res = StatusCodes.OK
            # case Commands.PREVIOUS:
            #     res = StatusCodes.OK
            case Commands.MUTE_TOGGLE:
                # await self._device.executor.mute(2)
                res = StatusCodes.OK
            case Commands.MUTE:
                # await self._device.executor.mute(1)
                res = StatusCodes.OK
            case Commands.UNMUTE:
                # await self._device.executor.mute(0)
                res = StatusCodes.OK

            case Commands.SELECT_SOUND_MODE:
                # sound_modes = self._device.sound_modes
                # upmixer = params.get("mode") if params else None
                # if not sound_modes or not upmixer:
                #     res = StatusCodes.BAD_REQUEST
                # else:
                #     # Reverse lookup: label -> key
                #     mode_key = next(
                #         (k for k, v in sound_modes.items() if v == upmixer), None
                #     )
                #     if not mode_key:
                #         res = StatusCodes.BAD_REQUEST
                #     else:
                #         await self._device.executor.upmixer(mode_key)
                #         res = StatusCodes.OK
                res = StatusCodes.OK

            case Commands.SELECT_SOURCE:
                # labels = self._device.source_list
                # label_name = params.get("source") if params else None
                # if not labels or not label_name:
                #     res = StatusCodes.BAD_REQUEST
                #     return res

                # index = next((k for k, v in labels.items() if v == label_name), None)
                # if index is None:
                #     res = StatusCodes.BAD_REQUEST
                # else:
                #     await self._device.executor.select_source(index)
                #     res = StatusCodes.OK
                res = StatusCodes.OK

            case Commands.VOLUME_DOWN:
                # await self._device.executor.volume_down()
                res = StatusCodes.OK

            case Commands.VOLUME_UP:
                # await self._device.executor.volume_up()
                res = StatusCodes.OK

            case Commands.VOLUME:
                # volume = int(params.get("volume")) if params else None
                # if volume is not None:
                #     await self._device.executor.volume(
                #         self._device.percent_to_db(volume)
                #     )
                #     res = StatusCodes.OK
                res = StatusCodes.OK

            case _:
                res = StatusCodes.BAD_REQUEST

        return res

    def filter_changed_attributes(self, update: dict[str, Any]) -> dict[Attributes, Any]:
        """
        Filter the given attributes and return only the changed values.

        :param update: dictionary with attributes.
        :return: filtered entity attributes containing changed attributes only.
        """
        attributes: dict[Attributes, Any] = {}
        # update[Attributes.SOUND_MODE_LIST] = list(self._device.sound_modes.values())
        # update[Attributes.SOURCE_LIST] = list(self._device.sound_modes.values())

        for key in (
            Attributes.MUTED,
            Attributes.SOUND_MODE,
            Attributes.SOUND_MODE_LIST,
            Attributes.SOURCE,
            Attributes.SOURCE_LIST,
            Attributes.STATE,
            Attributes.VOLUME,
        ):
            if key in update and key in self.attributes:
                if update[key] != self.attributes[key]:
                    attributes[key] = update[key]

        if Attributes.STATE in attributes:
            if attributes[Attributes.STATE] == States.OFF:
                attributes[Attributes.SOUND_MODE] = ""
                attributes[Attributes.SOUND_MODE_LIST] = []
                attributes[Attributes.SOURCE] = ""
                attributes[Attributes.SOURCE_LIST] = []

        if attributes:
            _LOG.debug("LyngdorfMediaPlayer update attributes %s -> %s", update, attributes)

        return attributes
