"""
Select entity functions for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from pylyngdorf.exceptions import LyngdorfProcessingError
from ucapi import EntityTypes, Select, StatusCodes
from ucapi.select import Attributes, Commands, States
from ucapi_framework import create_entity_id
from ucapi_framework.entity import Entity as FrameworkEntity

from const import LyngdorfConfig, LyngdorfSelectConfig
from device import LyngdorfDevice

_LOG = logging.getLogger(__name__)


class LyngdorfSelect(Select, FrameworkEntity):
    """Representation of a Lyngdorf Select entity."""

    def __init__(self, device_config: LyngdorfConfig, device: LyngdorfDevice, select_config: LyngdorfSelectConfig):
        """Initialize a Lyngdorf Select entity."""
        self._device = device
        self._entity_id = create_entity_id(EntityTypes.SELECT, device_config.identifier, select_config.identifier)
        self._select_config = select_config

        attributes: dict[str, Any] = {
            Attributes.STATE: States.UNAVAILABLE,
        }

        _LOG.debug("Initializing select entity: %s", self._entity_id)

        super().__init__(
            identifier=self._entity_id,
            name=f"{device_config.name} {select_config.name}",
            attributes=attributes,
            cmd_handler=self.cmd_handler,
        )

    async def cmd_handler(  # noqa: C901
        self,
        _entity: Select,
        cmd_id: str,
        params: dict[str, Any] | None,
        _websocket: Any = None,
    ) -> StatusCodes:
        """Handle select entity commands.

        Args:
            _entity: Select entity
            cmd_id: Command identifier
            params: Optional command parameters
            _websocket: Optional websocket connection

        Returns:
            StatusCodes: Result of command execution
        """
        # if self.attributes.get(Attributes.STATE, States.UNAVAILABLE) == States.UNAVAILABLE:
        #     return StatusCodes.OK
        _LOG.debug("[%s] Command: %s, params: %s", self._select_config.identifier, cmd_id, params)

        match cmd_id:
            case Commands.SELECT_OPTION:
                if params and "option" in params:
                    return await self.select_option(params["option"])
                return StatusCodes.BAD_REQUEST

            case Commands.SELECT_FIRST:
                options = self.attributes.get(Attributes.OPTIONS, [])
                if options:
                    return await self.select_option(options[0])
                return StatusCodes.BAD_REQUEST

            case Commands.SELECT_LAST:
                options = self.attributes.get(Attributes.OPTIONS, [])
                if options:
                    return await self.select_option(options[-1])
                return StatusCodes.BAD_REQUEST

            case Commands.SELECT_NEXT:
                options = self.attributes.get(Attributes.OPTIONS, [])
                current = self.attributes.get(Attributes.CURRENT_OPTION, "")

                if options and current in options:
                    cycle = params.get("cycle", False) if params else False
                    current_idx = options.index(current)
                    if current_idx < len(options) - 1:
                        return await self.select_option(options[current_idx + 1])
                    elif cycle:
                        return await self.select_option(options[0])
                    else:
                        return StatusCodes.OK
                return StatusCodes.BAD_REQUEST

            case Commands.SELECT_PREVIOUS:
                options = self.attributes.get(Attributes.OPTIONS, [])
                current = self.attributes.get(Attributes.CURRENT_OPTION, "")
                if options and current in options:
                    cycle = params.get("cycle", False) if params else False
                    current_idx = options.index(current)
                    if current_idx > 0:
                        return await self.select_option(options[current_idx - 1])
                    elif cycle:
                        return await self.select_option(options[-1])
                    else:
                        return StatusCodes.OK
                return StatusCodes.BAD_REQUEST

            case _:
                _LOG.warning("[%s] Unknown command: %s", self._select_config.identifier, cmd_id)
                return StatusCodes.NOT_IMPLEMENTED

    async def select_option(self, option: str) -> StatusCodes:
        """Handle option selection.

        Args:
            option: The selected option value

        Returns:
            StatusCodes: SUCCESS if command sent, ERROR otherwise
        """
        _LOG.debug("[%s] Selecting option: %s", self._select_config.identifier, option)

        try:
            await self._select_config.set_value_fn(self._device.receiver, option)

            _LOG.info("[%s] Successfully set to: %s", self._select_config.identifier, option)
            return StatusCodes.OK

        except LyngdorfProcessingError as err:
            _LOG.error(
                "[%s] Failed to select option %s: %s",
                self._select_config.identifier,
                option,
                err,
            )
            return StatusCodes.SERVER_ERROR
