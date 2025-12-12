"""
Registry for active Lyngdorf instances.

Used to store and retrieve device connections by device ID.
"""

from collections.abc import Iterator

from pylyngdorf.lyngdorf import Lyngdorf

_configured_lyngdorfs: dict[str, Lyngdorf] = {}


def get_device(device_id: str) -> Lyngdorf | None:
    """
    Retrieve the device associated with a given device ID.

    Args:
        device_id: Unique identifier for the Lyngdorf device.

    Returns:
        The corresponding Lyngdorf instance, or None if not found.
    """
    return _configured_lyngdorfs.get(device_id)


def register_device(device_id: str, device: Lyngdorf) -> None:
    """
    Register a Lyngdorf for a given device ID.

    Args:
        device_id: Unique identifier for the Lyngdorf device.
        device: Lyngdorf instance to associate with the device.
    """

    if device_id not in _configured_lyngdorfs:
        _configured_lyngdorfs[device_id] = device


def unregister_device(device_id: str) -> None:
    """
    Remove the device associated with the given device ID.

    Args:
        device_id: Unique identifier of the device to remove.
    """
    _configured_lyngdorfs.pop(device_id, None)


def all_devices() -> dict[str, Lyngdorf]:
    """
    Get a dictionary of all currently registered devices.

    Returns:
        A dictionary mapping device IDs to their Lyngdorf instances.
    """
    return _configured_lyngdorfs


def clear_devices() -> None:
    """
    Remove all registered devicess from the registry.
    """
    _configured_lyngdorfs.clear()


async def connect_all() -> None:
    """
    Connect all registered Lyngdorf instances asynchronously.
    """
    for device in iter_devices():
        await device.async_connect()


async def disconnect_all() -> None:
    """
    Disconnect all registered Lyngdorf instances asynchronously.
    """
    for device in iter_devices():
        await device.async_disconnect()


def iter_devices() -> Iterator[Lyngdorf]:
    """
    Yield each registered Lyngdorf instance.

    Returns:
        An iterator over all registered device objects.
    """
    return iter(_configured_lyngdorfs.values())
