"""
Registry for active LyngdorfDevice instances.

Used to store and retrieve device connections by device ID.
"""

from collections.abc import Iterator

from device import LyngdorfDevice

_configured_devices: dict[str, LyngdorfDevice] = {}


def get_device(device_id: str) -> LyngdorfDevice | None:
    """
    Retrieve the device associated with a given device ID.

    Args:
        device_id: Unique identifier for the Lyngdorf device.

    Returns:
        The corresponding LyngdorfDevice instance, or None if not found.
    """
    return _configured_devices.get(device_id)


def register_device(device_id: str, device: LyngdorfDevice) -> None:
    """
    Register a LyngdorfDevice for a given device ID.

    Args:
        device_id: Unique identifier for the Lyngdorf device.
        device: LyngdorfDevice instance to associate with the device.
    """

    if device_id not in _configured_devices:
        _configured_devices[device_id] = device


def unregister_device(device_id: str) -> None:
    """
    Remove the device associated with the given device ID.

    Args:
        device_id: Unique identifier of the device to remove.
    """
    _configured_devices.pop(device_id, None)


def all_devices() -> dict[str, LyngdorfDevice]:
    """
    Get a dictionary of all currently registered devices.

    Returns:
        A dictionary mapping device IDs to their LyngdorfDevice instances.
    """
    return _configured_devices


def clear_devices() -> None:
    """
    Remove all registered devicess from the registry.
    """
    _configured_devices.clear()


async def connect_all() -> None:
    """
    Connect all registered LyngdorfDevice instances asynchronously.
    """
    # for device in iter_devices():
    #     await device.connect()


async def disconnect_all() -> None:
    """
    Disconnect all registered LyngdorfDevice instances asynchronously.
    """
    # for device in iter_devices():
    #     await device.disconnect()


def iter_devices() -> Iterator[LyngdorfDevice]:
    """
    Yield each registered LyngdorfDevice instance.

    Returns:
        An iterator over all registered device objects.
    """
    return iter(_configured_devices.values())
