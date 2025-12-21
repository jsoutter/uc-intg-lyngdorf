"""
Discover Lyngdorf devices in local network using SZeroconfDDP protocol.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

from typing import Any

from ucapi_framework import DiscoveredDevice
from ucapi_framework.discovery import MDNSDiscovery
from zeroconf import IPVersion

from const import LYNGDORF_SERVICE_TYPE

_SERVICE_TYPE = "." + LYNGDORF_SERVICE_TYPE


class LyngdorfDiscovery(MDNSDiscovery):
    """mDNS discovery for Lyngdorf devices."""

    def parse_mdns_service(self, service_info: Any) -> DiscoveredDevice | None:
        """
        Parse mDNS service info into DiscoveredDevice.

        :param service_info: mDNS service info object from zeroconf
        :return: DiscoveredDevice or None if parsing fails
        """
        if not service_info.parsed_addresses():
            return None

        # Get the first IPv4 address
        addresses = service_info.parsed_addresses(version=IPVersion.V4Only)
        address = addresses[0] if addresses else None

        if not address:
            return None

        identifier = f"{address.replace('.', '-')}:{service_info.port}"

        # Extract name from service info (remove service suffix)
        name = service_info.name
        if name.endswith(_SERVICE_TYPE):
            name = name.replace(_SERVICE_TYPE, "")

        return DiscoveredDevice(
            identifier=identifier,
            name=name,
            address=address,
            extra_data={
                "port": service_info.port,
            },
        )
