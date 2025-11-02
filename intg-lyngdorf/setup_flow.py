"""
Setup flow for Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
from enum import IntEnum
from ipaddress import ip_address
from typing import Any

from ucapi import (
    AbortDriverSetup,
    DriverSetupRequest,
    IntegrationSetupError,
    RequestUserInput,
    SetupAction,
    SetupComplete,
    SetupDriver,
    SetupError,
    UserDataResponse,
)

import config
from config import LyngdorfDeviceConfig

# from device import LyngdorfDevice
from const import LYNGDORF_PORT, LYNGDORF_SERVICE_TYPE
from discover import ZeroconfDiscovery

# from registry import clear_devices

_LOG = logging.getLogger(__name__)


class SetupSteps(IntEnum):
    """Enumeration of setup steps to keep track of user data responses."""

    INIT = 0
    CONFIGURATION_MODE = 1
    DISCOVER = 2
    DEVICE_CHOICE = 3


# async def _handle_manual() -> RequestUserInput | SetupError:
async def _handle_manual(port: int = LYNGDORF_PORT) -> SetupAction:
    """
    Returns a form for manual configuration of IP and port.

    Args:
        port (int): Port number to prepopulate. Default is LYNGDORF_PORT.

    Returns:
        RequestUserInput: Form requesting user input for IP and port.
    """
    return RequestUserInput(
        {"en": "Lyngdorf Setup"},
        [
            {
                "id": "info",
                "label": {
                    "en": "Setup Information ",
                },
                "field": {
                    "label": {
                        "value": {
                            "en": ("Please supply the following settings for your Lyngdorf device."),
                        }
                    }
                },
            },
            {
                "field": {"text": {"value": ""}},
                "id": "host",
                "label": {
                    "en": "IP Address",
                },
            },
            {
                "field": {"number": {"value": port}},
                "id": "port",
                "label": {
                    "en": "Port:",
                },
            },
        ],
    )


async def driver_setup_handler(msg: SetupDriver) -> SetupAction:
    """
    Main entry point for handling all setup-related UCAPI messages.

    Args:
        msg (ucapi.SetupDriver): Message from UCAPI.

    Returns:
        ucapi.SetupAction: Action to take in response to the setup request.
    """
    global _setup_step

    if isinstance(msg, DriverSetupRequest):
        _setup_step = SetupSteps.INIT
        return await _handle_driver_setup(msg)
    if isinstance(msg, UserDataResponse):
        _LOG.debug("Setup handler message : step %s, message : %s", _setup_step, msg)
        if _setup_step == SetupSteps.CONFIGURATION_MODE and "action" in msg.input_values:
            return await _handle_configuration_mode(msg)
        if (
            _setup_step == SetupSteps.DISCOVER
            and "host" in msg.input_values
            and msg.input_values.get("host") != "manual"
        ):
            return await _handle_creation(msg)
        if (
            _setup_step == SetupSteps.DISCOVER
            and "host" in msg.input_values
            and msg.input_values.get("host") == "manual"
        ):
            return await _handle_manual()
        _LOG.error("No user input was received for step: %s", msg)

    elif isinstance(msg, AbortDriverSetup):
        _LOG.info("Setup was aborted with code: %s", msg.error)
        _setup_step = SetupSteps.INIT

    _LOG.error("Error during setup")
    return SetupError()


async def _handle_configuration_mode(msg: UserDataResponse) -> SetupAction:
    """
    Process user data response from the configuration mode screen.

    User input data:

    - ``choice`` contains identifier of selected device
    - ``action`` contains the selected action identifier

    :param msg: user input data from the configuration mode screen.
    :return: the setup action on how to continue
    """
    global _setup_step  # pylint: disable=global-statement
    global _cfg_add_device  # pylint: disable=global-statement

    action = msg.input_values["action"]

    # workaround for web-configurator not picking up first response
    await asyncio.sleep(1)

    match action:
        case "add":
            _cfg_add_device = True
            _setup_step = SetupSteps.DISCOVER
            return await _handle_discovery()
        case "remove":
            choice = msg.input_values["choice"]
            if config.devices and not config.devices.remove(choice):
                _LOG.warning("Could not remove device from configuration: %s", choice)
                return SetupError(error_type=IntegrationSetupError.OTHER)
            if config.devices:
                config.devices.store()
            return SetupComplete()
        case "reset":
            if config.devices:
                config.devices.clear()
            _setup_step = SetupSteps.DISCOVER
            return await _handle_discovery()
        case _:
            _LOG.error("Invalid configuration action: %s", action)
            return SetupError(error_type=IntegrationSetupError.OTHER)

    _setup_step = SetupSteps.DISCOVER
    return await _handle_discovery()


async def _handle_discovery() -> SetupAction:
    """
    Process user data response from the first setup process screen.
    """
    global _setup_step  # pylint: disable=global-statement

    zc = ZeroconfDiscovery()
    await zc.get(service_type=LYNGDORF_SERVICE_TYPE, response_wait_time=2)
    if len(zc.discovered) > 0:
        _LOG.debug("Found Lyngdorf devices")

        dropdown_devices: list[dict[str, Any]] = []
        for device in zc.discovered:
            dropdown_devices.append({"host": device.addresses[0], "label": {"en": f"{device.name.split('.', 1)[0]}"}})

        dropdown_devices.append({"host": "manual", "label": {"en": "Setup Manually"}})

        return RequestUserInput(
            {"en": "Discovered Lyngdorf devices"},
            [
                {
                    "field": {
                        "dropdown": {
                            "value": dropdown_devices[0]["host"],
                            "items": dropdown_devices,
                        }
                    },
                    "id": "host",
                    "label": {
                        "en": "Discovered Devices:",
                    },
                },
            ],
        )

    # Initial setup, make sure we have a clean configuration
    if (devices := config.devices) is not None:
        devices.clear()
    _setup_step = SetupSteps.DISCOVER
    return await _handle_manual()


async def _handle_driver_setup(msg: DriverSetupRequest) -> SetupAction:
    """
    Start driver setup.

    Initiated by Remote Two to set up the driver. The reconfigure flag determines the setup flow:

    - Reconfigure is True:
        show the configured devices and ask user what action to perform (add, delete, reset).
    - Reconfigure is False: clear the existing configuration and show device discovery screen.
      Ask user to enter ip address for manual configuration, otherwise auto-discovery is used.

    :param msg: driver setup request data, only `reconfigure` flag is of interest.
    :return: the setup action on how to continue
    """
    global _setup_step  # pylint: disable=global-statement

    reconfigure = msg.reconfigure
    _LOG.debug("Starting driver setup, reconfigure=%s", reconfigure)

    if reconfigure:
        _setup_step = SetupSteps.CONFIGURATION_MODE

        # get all configured devices for the user to choose from
        dropdown_devices: list[dict[str, Any]] = []
        if (devices := config.devices) is not None:
            for device in devices:
                dropdown_devices.append({"id": device.id, "label": {"en": f"{device.model}"}})

        dropdown_actions: list[dict[str, Any]] = [
            {
                "id": "add",
                "label": {
                    "en": "Add a new device",
                },
            },
        ]

        # add remove & reset actions if there's at least one configured device
        if dropdown_devices:
            dropdown_actions.append(
                {
                    "id": "remove",
                    "label": {
                        "en": "Delete selected device",
                    },
                },
            )
            dropdown_actions.append(
                {
                    "id": "reset",
                    "label": {
                        "en": "Reset configuration and reconfigure",
                    },
                },
            )
        else:
            # dummy entry if no devices are available
            dropdown_devices.append({"id": "", "label": {"en": "---"}})

        return RequestUserInput(
            {"en": "Configuration mode"},
            [
                {
                    "field": {
                        "dropdown": {
                            "value": dropdown_devices[0]["id"],
                            "items": dropdown_devices,
                        }
                    },
                    "id": "choice",
                    "label": {
                        "en": "Configured Devices",
                    },
                },
                {
                    "field": {
                        "dropdown": {
                            "value": dropdown_actions[0]["id"],
                            "items": dropdown_actions,
                        }
                    },
                    "id": "action",
                    "label": {
                        "en": "Action",
                    },
                },
            ],
        )

    # Initial setup, make sure we have a clean configuration
    if (devices := config.devices) is not None:
        devices.clear()
    _setup_step = SetupSteps.DISCOVER
    return await _handle_discovery()


async def _handle_creation(msg: UserDataResponse) -> SetupAction:
    """
    Process user data response from the first setup process screen.

    :param msg: response data from the requested user data
    :return: the setup action on how to continue
    """

    host = msg.input_values["host"]
    port = msg.input_values["port"]

    if host != "":
        try:
            ip_address(host)
        except ValueError:
            _LOG.error("The entered ip address %s is not valid", host)
            return SetupError(IntegrationSetupError.NOT_FOUND)

        _LOG.info("Entered ip address: %s", host)

        id = f"lyngdorf-{host.replace('.', '-')}"
        device = LyngdorfDeviceConfig(id, host, port, model="MP-60")
        if (devices := config.devices) is not None:
            devices.add(device)

        # # try:
        # #     # jvc = JvcProjector(ip, password=password)
        # #     # try:
        # #     #     await jvc.connect()
        # #     #     info = await jvc.get_info()
        # #     # finally:
        # #     #     await jvc.disconnect()
        # #     # _LOG.debug("JVC Projector info: %s", info)

        # #     # device = JVCDevice(
        # #     #     identifier=info.get("mac", info.get("model", "jvc")),
        # #     #     name=name,
        # #     #     address=ip,
        # #     #     password=password,
        # #     # )

        # #     config.devices.add(device)

        # # except Exception as ex:  # pylint: disable=broad-exception-caught
        # #     _LOG.error("Unable to connect at IP: %s. Exception: %s", ip, ex)
        # #     _LOG.info("Please check if you entered the correct ip of the projector")
        # #     return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
    else:
        _LOG.info("No host address entered")
        return SetupError(IntegrationSetupError.OTHER)
    _LOG.info("Setup complete")
    return SetupComplete()
