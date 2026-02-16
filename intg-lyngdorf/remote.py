"""
Remote entity functions for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any, Final

from ucapi import EntityTypes, Remote, StatusCodes, media_player
from ucapi.media_player import States as MediaStates
from ucapi.remote import Attributes, Commands, Features, States
from ucapi.remote import States as RemoteStates
from ucapi.ui import (
    Buttons,
    DeviceButtonMapping,
    Size,
    UiPage,
    create_btn_mapping,
    create_ui_text,
)
from ucapi_framework import create_entity_id
from ucapi_framework.entity import Entity as FrameworkEntity

from const import (
    MULTICHANNEL_MEDIA_PLAYER_COMMANDS_MAP,
    MULTICHANNEL_SIMPLE_COMMANDS_MAP,
    SIMPLE_COMMANDS_MAP,
    LyngdorfConfig,
    SimpleCommands,
)
from device import LyngdorfDevice

_LOG = logging.getLogger(__name__)

LYNGDORF_REMOTE_STATE_MAPPING: dict[str, str] = {
    MediaStates.UNKNOWN: RemoteStates.UNKNOWN,
    MediaStates.UNAVAILABLE: RemoteStates.UNAVAILABLE,
    MediaStates.OFF: RemoteStates.OFF,
    MediaStates.ON: RemoteStates.ON,
    MediaStates.BUFFERING: RemoteStates.ON,
    MediaStates.PLAYING: RemoteStates.ON,
    MediaStates.PAUSED: RemoteStates.ON,
}

BASE_COMMANDS: Final[tuple[media_player.Commands, ...]] = (
    media_player.Commands.VOLUME_UP,
    media_player.Commands.VOLUME_DOWN,
    media_player.Commands.MUTE_TOGGLE,
    media_player.Commands.MUTE,
    media_player.Commands.UNMUTE,
    media_player.Commands.PLAY_PAUSE,
    media_player.Commands.NEXT,
    media_player.Commands.PREVIOUS,
)


class LyngdorfRemote(Remote, FrameworkEntity):
    """Representation of a Lyngdorf Remote entity."""

    def __init__(self, device_config: LyngdorfConfig, device: LyngdorfDevice):
        """Initialize the class."""
        self._device: LyngdorfDevice = device
        self._entity_id = create_entity_id(EntityTypes.REMOTE, device_config.identifier)

        attributes: dict[str, Any] = {
            Attributes.STATE: States.UNAVAILABLE,
        }

        base_commands: list[str] = [cmd.value for cmd in BASE_COMMANDS] + [cmd.value for cmd in SimpleCommands]
        if device_config.multichannel:
            base_commands += list(MULTICHANNEL_MEDIA_PLAYER_COMMANDS_MAP.keys())
            base_commands += list(MULTICHANNEL_SIMPLE_COMMANDS_MAP.keys())
        self._simple_commands: list[str] = base_commands

        _LOG.debug("Initializing remote entity: %s", self._entity_id)

        super().__init__(
            self._entity_id,
            f"{device_config.name} Remote",
            features=[Features.SEND_CMD, Features.ON_OFF],
            attributes=attributes,
            simple_commands=self._simple_commands,
            button_mapping=self.create_button_mappings(device_config),
            ui_pages=self.create_ui(),
            cmd_handler=self.cmd_handler,
        )

    def map_entity_states(self, device_state: str) -> str:
        """Map media player states to remote states."""
        return LYNGDORF_REMOTE_STATE_MAPPING.get(device_state, RemoteStates.UNKNOWN)

    def get_int_param(self, param: str, params: dict[str, Any], default: int):
        """Get parameter in integer format."""
        try:
            value = params.get(param, default)
            if isinstance(value, int | float):
                return int(value)
            if isinstance(value, str) and value.strip():
                return int(float(value))
        except (ValueError, TypeError, AttributeError):
            pass
        return default

    async def cmd_handler(
        self,
        _entity: Remote,
        cmd_id: str,
        params: dict[str, Any] | None = None,
        _websocket: Any | None = None,
    ) -> StatusCodes:
        """
        Remote entity command handler.

        Called by the integration-API if a command is sent to a configured remote entity.

        :param cmd_id: command
        :param params: optional command parameters
        :return: status code of the command request
        """
        repeat = 1
        _LOG.info("Got %s command request: %s %s", self.id, cmd_id, params)

        if params:
            repeat = self.get_int_param("repeat", params, 1)

        for _ in range(repeat):
            await self.handle_command(cmd_id, params)

        return StatusCodes.OK

    async def handle_command(self, cmd_id: str, params: dict[str, Any] | None) -> StatusCodes:
        """Handle a remote command."""
        try:
            cmd = Commands(cmd_id)
        except ValueError:
            return StatusCodes.BAD_REQUEST

        try:
            if cmd in (Commands.ON, Commands.OFF):
                method = (
                    self._device.receiver.async_power_on
                    if cmd == Commands.ON
                    else self._device.receiver.async_power_off
                )
                await method()
                return StatusCodes.OK

            if params is None:
                return StatusCodes.BAD_REQUEST

            delay = params.get("delay", 0)

            if cmd == Commands.SEND_CMD:
                command = params.get("command")
                if not command:
                    return StatusCodes.BAD_REQUEST
                return await self.send_command(command, delay)

            if cmd == Commands.SEND_CMD_SEQUENCE:
                for command in params.get("sequence", []):
                    if (res := await self.send_command(command, delay)) != StatusCodes.OK:
                        return res
                return StatusCodes.OK

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as ex:
            _LOG.error("Error executing remote command %s: %s", cmd_id, ex)
            return StatusCodes.BAD_REQUEST

    async def send_command(self, command: str, delay: int) -> StatusCodes:  # noqa: C901
        """Send command."""
        if command not in self._simple_commands:
            return StatusCodes.BAD_REQUEST

        match command:
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
            case _:
                if (
                    mapped_cmd := SIMPLE_COMMANDS_MAP.get(command)
                    or MULTICHANNEL_MEDIA_PLAYER_COMMANDS_MAP.get(command)
                    or MULTICHANNEL_SIMPLE_COMMANDS_MAP.get(command)
                ):
                    await self._device.receiver.async_send_command(mapped_cmd)
                else:
                    return StatusCodes.NOT_IMPLEMENTED

        if delay > 0:
            await asyncio.sleep(delay)
        return StatusCodes.OK

    def create_button_mappings(self, config_device: LyngdorfConfig) -> list[DeviceButtonMapping | dict[str, Any]]:
        """Create button mappings."""
        button_mappings: list[DeviceButtonMapping | dict[str, Any]] = [
            create_btn_mapping(Buttons.VOLUME_UP, media_player.Commands.VOLUME_UP),
            create_btn_mapping(Buttons.VOLUME_DOWN, media_player.Commands.VOLUME_DOWN),
            create_btn_mapping(Buttons.MUTE, media_player.Commands.MUTE_TOGGLE),
            create_btn_mapping(Buttons.PLAY, media_player.Commands.PLAY_PAUSE),
            create_btn_mapping(Buttons.NEXT, media_player.Commands.NEXT),
            create_btn_mapping(Buttons.PREV, media_player.Commands.PREVIOUS),
        ]

        if config_device.multichannel:
            button_mappings += [
                create_btn_mapping(Buttons.DPAD_UP, media_player.Commands.CURSOR_UP),
                create_btn_mapping(Buttons.DPAD_DOWN, media_player.Commands.CURSOR_DOWN),
                create_btn_mapping(Buttons.DPAD_LEFT, media_player.Commands.CURSOR_LEFT),
                create_btn_mapping(Buttons.DPAD_RIGHT, media_player.Commands.CURSOR_RIGHT),
                create_btn_mapping(Buttons.DPAD_MIDDLE, media_player.Commands.CURSOR_ENTER),
                create_btn_mapping(Buttons.MENU, media_player.Commands.MENU),
                create_btn_mapping(Buttons.BACK, media_player.Commands.BACK),
            ]

        for item in button_mappings:
            _LOG.debug(item)
        return button_mappings

    def create_ui(self) -> list[UiPage | dict[str, Any]]:
        """Create a user interface with common commands."""
        ui_page1 = UiPage("page1", "Commands", grid=Size(2, 6))
        ui_page1.add(create_ui_text("Previous Source", 0, 0, Size(1, 1), SimpleCommands.SOURCE_PREV))
        ui_page1.add(create_ui_text("Next Source", 1, 0, Size(1, 1), SimpleCommands.SOURCE_PREV))
        ui_page1.add(create_ui_text("Previous Voicing", 0, 1, Size(1, 1), SimpleCommands.VOICING_NEXT))
        ui_page1.add(create_ui_text("Next Voicing", 1, 1, Size(1, 1), SimpleCommands.VOICING_PREV))
        ui_page1.add(create_ui_text("Previous Focus Position", 0, 2, Size(1, 1), SimpleCommands.FOCUS_POSITION_NEXT))
        ui_page1.add(create_ui_text("Next Focus Position", 1, 2, Size(1, 1), SimpleCommands.FOCUS_POSITION_PREV))

        return [ui_page1]
