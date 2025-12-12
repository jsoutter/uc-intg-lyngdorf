"""
Remote entity functions.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from pylyngdorf.lyngdorf import Lyngdorf
from ucapi import EntityTypes, Remote, StatusCodes
from ucapi.media_player import Attributes as MediaAttributes
from ucapi.media_player import States as MediaStates
from ucapi.remote import Attributes, Commands, States
from ucapi.ui import (
    Buttons,
    DeviceButtonMapping,
    EntityCommand,
    Size,
    UiPage,
    create_btn_mapping,
    create_ui_icon,
    create_ui_text,
)

from config import LyngdorfDeviceConfig, create_entity_id
from const import RemoteDef, SimpleCommands
from const import SimpleCommands as cmds

_LOG = logging.getLogger(__name__)

REMOTE_STATE_MAPPING = {
    MediaStates.OFF: States.OFF,
    MediaStates.ON: States.ON,
    MediaStates.STANDBY: States.OFF,
    MediaStates.UNAVAILABLE: States.UNAVAILABLE,
    MediaStates.UNKNOWN: States.UNKNOWN,
}


class LyngdorfRemote(Remote):
    """Representation of a Lyngdorf Remote entity."""

    def __init__(self, config_device: LyngdorfDeviceConfig, device: Lyngdorf):
        """Initialize the class."""
        self._device = device
        entity_id = create_entity_id(config_device.identifier, EntityTypes.REMOTE)
        features = RemoteDef.features
        attributes = RemoteDef.attributes
        super().__init__(
            entity_id,
            f"{config_device.model} Remote",
            features,
            attributes,
            simple_commands=RemoteDef.simple_commands,
            button_mapping=self.create_button_mappings(),
            ui_pages=self.create_ui(),
        )

        _LOG.debug("LyngdorfRemote init %s : %s", entity_id, attributes)

    def create_button_mappings(self) -> list[DeviceButtonMapping | dict[str, Any]]:
        """Create button mappings."""

        button_mappings: list[DeviceButtonMapping | dict[str, Any]] = [
            create_btn_mapping(Buttons.VOLUME_UP, cmds.VOLUME_UP.name),
            create_btn_mapping(Buttons.VOLUME_DOWN, cmds.VOLUME_DOWN.name),
            create_btn_mapping(Buttons.MUTE, cmds.MUTE_TOGGLE.name),
            create_btn_mapping(Buttons.DPAD_UP, cmds.UP.name),
            create_btn_mapping(Buttons.DPAD_DOWN, cmds.DOWN.name),
            create_btn_mapping(Buttons.DPAD_LEFT, cmds.LEFT.name),
            create_btn_mapping(Buttons.DPAD_RIGHT, cmds.RIGHT.name),
            create_btn_mapping(Buttons.DPAD_MIDDLE, cmds.ENTER.name),
            create_btn_mapping(Buttons.BACK, cmds.BACK.name),
            DeviceButtonMapping(button="MENU", short_press=EntityCommand(cmd_id="MENU")),
        ]

        for item in button_mappings:
            _LOG.debug(item)
        return button_mappings

    def create_ui(self) -> list[UiPage | dict[str, Any]]:
        """Create a user interface with different pages that includes all commands"""

        ui_page1 = UiPage("page1", "Power & Input", grid=Size(6, 6))
        ui_page1.add(create_ui_text("Power On", 0, 0, Size(6, 1), Commands.ON))
        ui_page1.add(create_ui_text("1", 0, 1, Size(2, 1), cmds.DIGIT_1.name))
        ui_page1.add(create_ui_text("2", 2, 1, Size(2, 1), cmds.DIGIT_2.name))
        ui_page1.add(create_ui_text("3", 4, 1, Size(2, 1), cmds.DIGIT_3.name))
        ui_page1.add(create_ui_text("4", 0, 2, Size(2, 1), cmds.DIGIT_4.name))
        ui_page1.add(create_ui_text("5", 2, 2, Size(2, 1), cmds.DIGIT_5.name))
        ui_page1.add(create_ui_text("6", 4, 2, Size(2, 1), cmds.DIGIT_6.name))
        ui_page1.add(create_ui_text("7", 0, 3, Size(2, 1), cmds.DIGIT_7.name))
        ui_page1.add(create_ui_text("8", 2, 3, Size(2, 1), cmds.DIGIT_8.name))
        ui_page1.add(create_ui_text("9", 4, 3, Size(2, 1), cmds.DIGIT_9.name))
        ui_page1.add(create_ui_text("SRC -", 0, 4, Size(2, 1), cmds.SRC_DOWN.name))
        ui_page1.add(create_ui_text("0", 2, 4, Size(2, 1), cmds.DIGIT_0.name))
        ui_page1.add(create_ui_text("SRC +", 4, 4, Size(2, 1), cmds.SRC_UP.name))
        ui_page1.add(create_ui_text("Standby", 0, 5, Size(6, 1), Commands.OFF))

        ui_page2 = UiPage("page2", "Configuration", grid=Size(6, 6))
        ui_page2.add(create_ui_text("Setup", 0, 0, Size(6, 1), cmds.SETUP.name))
        ui_page2.add(create_ui_icon("uc:up-arrow", 2, 1, Size(2, 1), cmds.UP.name))
        ui_page2.add(create_ui_icon("uc:left-arrow", 0, 2, Size(2, 1), cmds.LEFT.name))
        ui_page2.add(create_ui_icon("uc:circle", 2, 2, Size(2, 1), cmds.ENTER.name))
        ui_page2.add(create_ui_icon("uc:right-arrow", 4, 2, Size(2, 1), cmds.RIGHT.name))
        ui_page2.add(create_ui_icon("uc:down-arrow", 2, 3, Size(2, 1), cmds.DOWN.name))
        ui_page2.add(create_ui_text("Back", 0, 4, Size(2, 1), cmds.BACK.name))
        ui_page2.add(create_ui_text("Menu", 4, 4, Size(2, 1), cmds.MENU.name))

        return [ui_page1, ui_page2]

    async def command(self, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """
        Handle command requests from the integration API for the remote entity.
        """
        params = params or {}

        simple_cmd: str | None = params.get("command")
        if simple_cmd and simple_cmd.startswith("remote"):
            cmd_id = simple_cmd.split(".")[1]

        _LOG.info(
            "Received Remote command request: %s with parameters: %s",
            cmd_id,
            params or "no parameters",
        )

        status = StatusCodes.BAD_REQUEST  # Default fallback

        try:
            cmd = Commands(cmd_id)
            _LOG.debug("Resolved command: %s", cmd)
        except ValueError:
            status = StatusCodes.NOT_IMPLEMENTED
        else:
            match cmd:
                # case Commands.ON:
                #     status = await self._device.power_on()

                # case Commands.OFF:
                #     status = await self._device.power_off()

                case Commands.SEND_CMD:
                    if not simple_cmd:
                        _LOG.warning("Missing command in SEND_CMD")
                        status = StatusCodes.BAD_REQUEST
                    else:
                        command_enum: SimpleCommands | None = None
                        if simple_cmd in cmds.__members__:
                            command_enum = cmds[simple_cmd]
                            _LOG.debug("Resolved command: %s", command_enum)

                        status = StatusCodes.OK

                case _:
                    status = StatusCodes.NOT_IMPLEMENTED

            #             case Commands.SEND_CMD:
            #                 if not simple_cmd:
            #                     _LOG.warning("Missing command in SEND_CMD")
            #                     status = StatusCodes.BAD_REQUEST
            #                 else:
            #                     command_enum = None

            #                 # First: try direct enum name match (e.g. "LEFT")
            #                 if simple_cmd in cmds.__members__:
            #                     command_enum = cmds[simple_cmd]

            #                 else:
            #                     # Second: try display_name match (e.g. "1.85", "4x3")
            #                     for cmd in cmds:
            #                         if cmd.display_name == simple_cmd:
            #                             command_enum = cmd
            #                             break

            #                 if command_enum:
            #                     actual_cmd = command_enum.value
            #                     cmd_params = None

            #                     if actual_cmd.isdigit() and 0 <= int(actual_cmd) <= 10:
            #                         actual_cmd = f"send_{actual_cmd}"
            #                     elif actual_cmd == "display_message":
            #                         cmd_params = {
            #                             "timeout": 3,
            #                             "message": "This is a Test Message from the UC Remote.",
            #                         }
            #                     elif actual_cmd == "input":
            #                         try:
            #                             index = self._device.source_list.index(self._device.source)
            #                             cmd_params = (index,)
            #                         except ValueError:
            #                             _LOG.warning("Current source not in source list")
            #                             actual_cmd = None
            #                             status = StatusCodes.BAD_REQUEST

            #                     if actual_cmd:
            #                         status = await self._device.send_command(actual_cmd, cmd_params)
            #                 else:
            #                     _LOG.warning("Unknown command: %s", simple_cmd)
            #                     status = StatusCodes.NOT_IMPLEMENTED

        return status

    def filter_changed_attributes(self, update: dict[str, Any]) -> dict[Attributes, Any]:
        """
        Filter the given media-player attributes and return remote attributes with converted state.

        :param update: dictionary with MediaAttributes.
        :return: dictionary with changed remote.Attributes only.
        """
        if MediaAttributes.STATE not in update:
            return {}

        media_state = update[MediaAttributes.STATE]
        new_state = REMOTE_STATE_MAPPING.get(media_state, States.UNKNOWN)

        if Attributes.STATE not in self.attributes or self.attributes[Attributes.STATE] != new_state:
            result = {Attributes.STATE: new_state}
        else:
            result = {}

        _LOG.debug(
            "Remote state changed from %s to %s based on media update %s",
            self.attributes.get(Attributes.STATE),
            new_state,
            update,
        )
        return result
