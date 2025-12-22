"""
Setup flow for Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from ipaddress import ip_address
from typing import Any

from pylyngdorf.const import DEFAULT_PORT
from pylyngdorf.lyngdorf import Lyngdorf
from ucapi import IntegrationSetupError, RequestUserInput, SetupError
from ucapi_framework import BaseSetupFlow

from const import LyngdorfConfig

_LOG = logging.getLogger(__name__)


def _handle_manual(port: int = DEFAULT_PORT) -> RequestUserInput:
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
                    "en": "Setup your Lyngdorf device",
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
                "id": "name",
                "label": {
                    "en": "Device Name",
                },
            },
            {
                "field": {"text": {"value": ""}},
                "id": "address",
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


class LyngdorfSetupFlow(BaseSetupFlow[LyngdorfConfig]):
    """
    Setup flow for Lyngdorf integration.

    Handles Lyngdorf device configuration through mDNS/Zeroconf discovery or manual entry.
    """

    def get_manual_entry_form(self) -> RequestUserInput:
        """
        Return the manual entry form for device setup.

        :return: RequestUserInput with form fields for manual configuration
        """
        return _handle_manual()

    async def query_device(self, input_values: dict[str, Any]) -> LyngdorfConfig | RequestUserInput | SetupError:
        name = (input_values.get("name", "")).strip()
        address = input_values.get("address", "").strip()
        port = input_values.get("port", DEFAULT_PORT)

        if not address:
            # Re-display the form if address is missing
            _LOG.warning("Address is required, re-displaying form")
            return _handle_manual(port)

        try:
            address = ip_address(address).compressed
        except ValueError:
            _LOG.error("Invalid IP address provided: %s", address)
            return _handle_manual(port)

        try:
            receiver: Lyngdorf = Lyngdorf.create(address, port)
            try:
                await receiver.async_connect()
            finally:
                await receiver.async_disconnect()

            if model := receiver.model:
                self.model = model.value
            else:
                _LOG.error("Unsupported device at IP: %s.", address)
                return SetupError(IntegrationSetupError.OTHER)

            identifier = f"{address.replace('.', '-')}:{port}"

            return LyngdorfConfig(
                identifier=identifier,
                name=name,
                address=address,
                port=port,
                model=model.value,
                multichannel=receiver.multichannel,
            )

        except Exception as ex:  # pylint: disable=broad-exception-caught
            _LOG.error("Unable to connect at IP: %s. Exception: %s", address, ex)
            _LOG.info("Please check if you entered the correct ip of the Lyngdorf device")
            return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
