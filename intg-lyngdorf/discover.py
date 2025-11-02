"""
Discovery module for Zeroconf protocol.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
from dataclasses import dataclass

from zeroconf import IPVersion, ServiceListener, Zeroconf
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo, AsyncZeroconf

DEFAULT_RESPONSE_WAIT_TIME = 4.0


@dataclass
class ZeroconfResponseInfo:
    """
    This class is used to store information about a response received from the Zeroconf protocol.
    It contains the datagram and the address of the sender.
    """

    def __init__(
        self,
        name: str,
        addresses: list[str],
        port: int | None = None,
        server: str | None = None,
    ):
        self.name = name
        self.addresses = addresses
        self.port = port
        self.server = server

    def __repr__(self):
        return (
            f"ZeroconfResponseInfo(name={self.name}, addresses={self.addresses}, "
            f"port={self.port}, server={self.server})"
        )


class ZeroconfServiceListener(ServiceListener):
    """Listener that schedules async service resolution tasks."""

    def __init__(self, zeroconf: Zeroconf):
        self.zeroconf = zeroconf
        self.services: dict[str, AsyncServiceInfo] = {}

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        asyncio.create_task(self.resolve_service(type_, name))

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self.services.pop(name, None)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        asyncio.create_task(self.resolve_service(type_, name))

    async def resolve_service(self, type_: str, name: str) -> None:
        info = AsyncServiceInfo(type_, name)
        ok = await info.async_request(self.zeroconf, timeout=1000)
        if ok:
            self.services[name] = info


class ZeroconfDiscovery:
    """This class is used to store services discovered using the Zeroconf protocol."""

    def __init__(self):
        self.discovered: list[ZeroconfResponseInfo] = []

    async def get(
        self,
        service_type: str,
        response_wait_time: float = DEFAULT_RESPONSE_WAIT_TIME,
    ) -> None:
        """
        Discover services asynchronously for a given duration (seconds).
        Uses AsyncServiceInfo.async_request() to resolve discovered services.
        """
        async with AsyncZeroconf() as azc:
            listener = ZeroconfServiceListener(azc.zeroconf)
            browser = AsyncServiceBrowser(azc.zeroconf, service_type, listener)

            await asyncio.sleep(response_wait_time)
            await browser.async_cancel()

            for name, response_info in listener.services.items():
                info = ZeroconfResponseInfo(
                    name,
                    response_info.parsed_addresses(IPVersion.V4Only),
                    response_info.port,
                    response_info.server,
                )
                self.discovered.append(info)
