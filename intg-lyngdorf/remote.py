"""
Remote entity functions for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import EntityTypes, Remote, StatusCodes
from ucapi.remote import Attributes, Commands, Features

# from ucapi.ui import (
#     Buttons,
#     DeviceButtonMapping,
#     EntityCommand,
#     Size,
#     UiPage,
#     create_btn_mapping,
#     create_ui_icon,
#     create_ui_text,
# )
from ucapi_framework import create_entity_id

from const import LyngdorfConfig

# from const import SimpleCommands as cmds
from device import LyngdorfDevice

_LOG = logging.getLogger(__name__)

features = [
    # Features.SEND_CMD,
    Features.ON_OFF,
]


class LyngdorfRemote(Remote):
    """Representation of a Lyngdorf Remote entity."""

    def __init__(self, config_device: LyngdorfConfig, device: LyngdorfDevice):
        """Initialize the class."""
        self._device = device
        entity_id = create_entity_id(EntityTypes.REMOTE, config_device.identifier)

        _LOG.debug("Initializing remote entity: %s", entity_id)

        super().__init__(
            entity_id,
            f"{config_device.name} Remote",
            features,
            attributes={
                Attributes.STATE: device.state,
            },
            # simple_commands=RemoteDef.simple_commands,
            # button_mapping=self.create_button_mappings(),
            # ui_pages=self.create_ui(),
            cmd_handler=self.cmd_handler,
        )

    async def cmd_handler(
        self, entity: Remote, cmd_id: str, params: dict[str, Any] | None, websocket: Any
    ) -> StatusCodes:
        """
        Remote entity command handler.

        Called by the integration-API if a command is sent to a configured remote entity.

        :param cmd_id: command
        :param params: optional command parameters
        :return: status code of the command request
        """
        _LOG.info("Got %s command request: %s %s", self.id, cmd_id, params if params else "")

        try:
            cmd = Commands(cmd_id)
        except ValueError:
            return StatusCodes.BAD_REQUEST

        else:
            match cmd:
                case Commands.ON:
                    await self._device.receiver.async_power_on()
                case Commands.OFF:
                    await self._device.receiver.async_power_off()
                # case Commands.SEND_CMD:
                case _:
                    return StatusCodes.NOT_IMPLEMENTED

        return StatusCodes.OK

    # def create_button_mappings(self) -> list[DeviceButtonMapping | dict[str, Any]]:
    #     """Create button mappings."""

    #     button_mappings: list[DeviceButtonMapping | dict[str, Any]] = [
    #         create_btn_mapping(Buttons.VOLUME_UP, cmds.VOLUME_UP.name),
    #         create_btn_mapping(Buttons.VOLUME_DOWN, cmds.VOLUME_DOWN.name),
    #         create_btn_mapping(Buttons.MUTE, cmds.MUTE_TOGGLE.name),
    #         create_btn_mapping(Buttons.DPAD_UP, cmds.UP.name),
    #         create_btn_mapping(Buttons.DPAD_DOWN, cmds.DOWN.name),
    #         create_btn_mapping(Buttons.DPAD_LEFT, cmds.LEFT.name),
    #         create_btn_mapping(Buttons.DPAD_RIGHT, cmds.RIGHT.name),
    #         create_btn_mapping(Buttons.DPAD_MIDDLE, cmds.ENTER.name),
    #         create_btn_mapping(Buttons.BACK, cmds.BACK.name),
    #         DeviceButtonMapping(button="MENU", short_press=EntityCommand(cmd_id="MENU")),
    #     ]

    #     for item in button_mappings:
    #         _LOG.debug(item)
    #     return button_mappings

    # def create_ui(self) -> list[UiPage | dict[str, Any]]:
    #     """Create a user interface with different pages that includes all commands"""

    #     ui_page1 = UiPage("page1", "Power & Input", grid=Size(6, 6))
    #     ui_page1.add(create_ui_text("Power On", 0, 0, Size(6, 1), Commands.ON))
    #     ui_page1.add(create_ui_text("1", 0, 1, Size(2, 1), cmds.DIGIT_1.name))
    #     ui_page1.add(create_ui_text("2", 2, 1, Size(2, 1), cmds.DIGIT_2.name))
    #     ui_page1.add(create_ui_text("3", 4, 1, Size(2, 1), cmds.DIGIT_3.name))
    #     ui_page1.add(create_ui_text("4", 0, 2, Size(2, 1), cmds.DIGIT_4.name))
    #     ui_page1.add(create_ui_text("5", 2, 2, Size(2, 1), cmds.DIGIT_5.name))
    #     ui_page1.add(create_ui_text("6", 4, 2, Size(2, 1), cmds.DIGIT_6.name))
    #     ui_page1.add(create_ui_text("7", 0, 3, Size(2, 1), cmds.DIGIT_7.name))
    #     ui_page1.add(create_ui_text("8", 2, 3, Size(2, 1), cmds.DIGIT_8.name))
    #     ui_page1.add(create_ui_text("9", 4, 3, Size(2, 1), cmds.DIGIT_9.name))
    #     ui_page1.add(create_ui_text("SRC -", 0, 4, Size(2, 1), cmds.SRC_DOWN.name))
    #     ui_page1.add(create_ui_text("0", 2, 4, Size(2, 1), cmds.DIGIT_0.name))
    #     ui_page1.add(create_ui_text("SRC +", 4, 4, Size(2, 1), cmds.SRC_UP.name))
    #     ui_page1.add(create_ui_text("Standby", 0, 5, Size(6, 1), Commands.OFF))

    #     ui_page2 = UiPage("page2", "Configuration", grid=Size(6, 6))
    #     ui_page2.add(create_ui_text("Setup", 0, 0, Size(6, 1), cmds.SETUP.name))
    #     ui_page2.add(create_ui_icon("uc:up-arrow", 2, 1, Size(2, 1), cmds.UP.name))
    #     ui_page2.add(create_ui_icon("uc:left-arrow", 0, 2, Size(2, 1), cmds.LEFT.name))
    #     ui_page2.add(create_ui_icon("uc:circle", 2, 2, Size(2, 1), cmds.ENTER.name))
    #     ui_page2.add(create_ui_icon("uc:right-arrow", 4, 2, Size(2, 1), cmds.RIGHT.name))
    #     ui_page2.add(create_ui_icon("uc:down-arrow", 2, 3, Size(2, 1), cmds.DOWN.name))
    #     ui_page2.add(create_ui_text("Back", 0, 4, Size(2, 1), cmds.BACK.name))
    #     ui_page2.add(create_ui_text("Menu", 4, 4, Size(2, 1), cmds.MENU.name))

    #     return [ui_page1, ui_page2]
