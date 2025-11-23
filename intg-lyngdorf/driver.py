#!/usr/bin/env python3
"""
This module implements a Remote Two/3 integration driver for Lyngdorf processors.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

import ucapi
from ucapi.media_player import Attributes as MediaAttr
from ucapi.media_player import States
from ucapi.sensor import Attributes as SensorAttr

import config
from api import api, loop
from config import LyngdorfConfigDevice
from const import SensorEntityPrefix
from device import LyngdorfDevice
from media_player import LyngdorfMediaPlayer
from registry import (
    all_devices,
    clear_devices,
    connect_all,
    disconnect_all,
    get_device,
    register_device,
    unregister_device,
)
from remote import REMOTE_STATE_MAPPING, LyngdorfRemote
from sensor import LyngdorfSensor

# from sensor import LyngdorfSensor
from setup_flow import driver_setup_handler
from utils import setup_logger

_LOG = logging.getLogger("driver")


@api.listens_to(ucapi.Events.CONNECT)
async def on_connect() -> None:
    """Connect all configured receivers when the Remote Two sends the connect command."""
    _LOG.info("Received connect event message from remote")
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)
    loop.create_task(connect_all())


@api.listens_to(ucapi.Events.DISCONNECT)
async def on_r2_disconnect() -> None:
    """Disconnect notification from the Remote Two."""

    _LOG.info("Received disconnect event message from remote")
    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)
    loop.create_task(disconnect_all())


@api.listens_to(ucapi.Events.ENTER_STANDBY)
async def on_r2_enter_standby() -> None:
    """
    Enter standby notification from Remote Two.

    Disconnect every Lyngdorf instance.
    """

    _LOG.debug("Enter standby event: disconnecting device(s)")
    loop.create_task(disconnect_all())


@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_r2_exit_standby() -> None:
    """
    Exit standby notification from Remote Two.

    Connect all Lyngdorf instances.
    """

    _LOG.debug("Exit standby event: connecting device(s)")
    loop.create_task(connect_all())


@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """
    _LOG.debug("Subscribe entities event: %s", entity_ids)

    if not entity_ids:
        return

    # Assume all entities share the same device
    first_entity = api.configured_entities.get(entity_ids[0])
    if not first_entity:
        _LOG.error("First entity %s not found in configured_entities", entity_ids[0])
        return

    # device_id = config.device_from_entity_id(first_entity)
    # device = get_device(device_id)

    # if not device:
    #     fallback_device = config.devices.get(device_id)
    #     if fallback_device:
    #         _configure_new_lyngdorf(fallback_device, connect=True)
    #     else:
    #         _LOG.error("Failed to subscribe entities: no Lyngdorf configuration found for %s", device_id)
    #     return

    for entity_id in entity_ids:
        _LOG.debug("entity id = %s", entity_id)
        entity = api.configured_entities.get(entity_id)
        if not entity:
            continue

        #     # Handle Lyngdorf Sensor entities
        if isinstance(entity, LyngdorfSensor):
            _LOG.info("Setting initial state of Lyngdorf Sensor %s", entity_id)

            if entity_id.startswith(SensorEntityPrefix.VOLUME.value):
                pass
                # value = ""
                # if device.device_info:
                #     value = device.device_info.current_source_content_aspect
                # api.configured_entities.update_attributes(
                #     entity_id, {SensorAttr.STATE: States.ON, SensorAttr.VALUE: value, SensorAttr.UNIT: ""}
                # )

            current_value = entity.attributes.get(SensorAttr.VALUE, "unknown")
            _LOG.info("Updated Lyngdorf Sensor entity %s with value %s", entity_id, current_value)
            continue

    # Handle media_player or remote entities
    # _update_entity_attributes(entity_id, entity, device.attributes)


def _update_entity_attributes(entity_id: str, entity, attributes: dict):
    """
    Update attributes for the given entity based on its type.
    """
    # if isinstance(entity, LyngdorfMediaPlayer):
    #     api.configured_entities.update_attributes(entity_id, attributes)
    # elif isinstance(entity, LyngdorfRemote):
    #     api.configured_entities.update_attributes(
    #         entity_id,
    #         {ucapi.remote.Attributes.STATE: REMOTE_STATE_MAPPING.get(attributes.get(MediaAttr.STATE, States.UNKNOWN))},
    #     )


@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """On unsubscribe, disconnect devices only if no other entities are using them."""
    _LOG.debug("Unsubscribe entities event: %s", entity_ids)

    # Collect devices associated with the entities being unsubscribed
    devices_to_remove = {
        config.extract_device_id(entity)
        for entity in (api.configured_entities.get(eid) for eid in entity_ids)
        if entity is not None
    }

    # Check other remaining entities to see if they still use these devices
    remaining_entities = [e for e in api.configured_entities.get_all() if e.get("entity_id") not in entity_ids]
    _LOG.debug(f"remaining_entities={remaining_entities}")

    # for entity in remaining_entities:
    #     device_id = config.extract_device_id(entity)
    #     devices_to_remove.discard(device_id)  # discard safely removes if present

    # Disconnect and clean up devices no longer in use
    for device_id in devices_to_remove:
        if device_id in all_devices():
            device = get_device(device_id)
            # await device.disconnect()
            # device.events.remove_all_listeners()


def _configure_new_lyngdorf(config: LyngdorfConfigDevice, connect: bool = False) -> None:
    """
    Create and configure a new Lyngdorf device.

    If a device already exists for the given device ID, reuse it.
    Otherwise, create and register a new one.

    :param config: The Lyngdorf device configuration.
    :param connect: Whether to initiate connection immediately.
    """

    device = get_device(config.identifier)

    # if device:
    #     device.disconnect()
    # else:
    #     device = LyngdorfDevice(info.address, info.port, device_id=info.id)

    #     device.events.on(Events.CONNECTED.name, on_lyngdorf_connected)
    #     device.events.on(Events.DISCONNECTED.name, on_lyngdorf_disconnected)
    #     device.events.on(Events.UPDATE.name, on_lyngdorf_update)

    #     register_device(info.id, device)
    #     _LOG.debug("Registered device: %s", device)

    # if connect:
    #     loop.create_task(device.connect())

    _register_available_entities(config, device)


def _register_available_entities(config: LyngdorfConfigDevice, device: LyngdorfDevice) -> None:
    """
    Register remote and media player entities for a Lyngdorf device and associate its device.

    :param info: Lyngdorf configuration
    :param device: Active LyngdorfDevice for the device
    """
    for entity_cls in (LyngdorfRemote, LyngdorfMediaPlayer):
        entity = entity_cls(config, device)
        if api.available_entities.contains(entity.id):
            api.available_entities.remove(entity.id)
        api.available_entities.add(entity)

    for sensor in [
        SensorEntityPrefix.VOLUME,
    ]:
        entity = LyngdorfSensor(config, sensor.value)

        if api.available_entities.contains(entity.id):
            api.available_entities.remove(entity.id)

        api.available_entities.add(entity)


async def on_lyngdorf_connected(device_id: str):
    """Handle Lyngdorf connection."""
    _LOG.debug("Lyngdorf connected: %s", device_id)

    if not get_device(device_id):
        _LOG.warning("Lyngdorf %s is not configured", device_id)
        return

    await api.set_device_state(ucapi.DeviceStates.CONNECTED)


async def on_lyngdorf_disconnected(device_id: str):
    """Handle Lyngdorf disconnection."""
    _LOG.debug("Lyngdorf disconnected: %s", device_id)

    if not get_device(device_id):
        _LOG.warning("Lyngdorf %s is not configured", device_id)
        return

    device = get_device(device_id)
    _LOG.debug(device)

    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)


async def on_lyngdorf_update(entity_id: str, update: dict[str, Any] | None) -> None:
    """
    Update attributes of configured media-player or remote entity if device attributes changed.

    :param device_id: Device identifier.
    :param update: Dictionary containing the updated attributes or None.
    """
    if update is None:
        return

    device_id = entity_id.split(".", 1)[1]
    device = get_device(device_id)
    if device is None:
        return

    _LOG.debug("[%s] Update............: %s", entity_id, update)

    # entity: LyngdorfMediaPlayer | LyngdorfRemote | None = api.configured_entities.get(entity_id)
    # if entity is None:
    #     _LOG.debug("Entity %s not found", entity_id)
    #     return

    # changed_attrs = entity.filter_changed_attributes(update)
    # if changed_attrs:
    #     _LOG.debug("Changed Attrs: %s, %s", entity_id, changed_attrs)
    #     api_update_attributes = api.configured_entities.update_attributes(entity_id, changed_attrs)
    #     _LOG.debug("api_update_attributes = %s", api_update_attributes)
    # else:
    #     _LOG.debug("attributes not changed")


def on_device_added(device: LyngdorfConfigDevice) -> None:
    """Handle a newly added device in the configuration."""
    _LOG.debug("New Lyngdorf device added: %s", device)
    loop.create_task(api.set_device_state(ucapi.DeviceStates.CONNECTED))
    _configure_new_lyngdorf(device, connect=False)


def on_device_removed(device: LyngdorfConfigDevice | None) -> None:
    """Handle removal of a Lyngdorf device from config."""
    if device is None:
        _LOG.info("All devices cleared from config.")
        clear_devices()
        api.configured_entities.clear()
        api.available_entities.clear()
        return

    # device = get_device(device.id)
    # if device:
    #     unregister_device(device.id)
    #     loop.create_task(_async_remove(device))
    #     api.configured_entities.remove(f"media_player.{device.id}")
    #     api.configured_entities.remove(f"remote.{device.id}")
    #     _LOG.info("Device for device_id %s cleaned up", device.id)
    # else:
    #     _LOG.debug("No Device found for removed device %s", device.id)


# async def _async_remove(device: LyngdorfDevice) -> None:
#     """Disconnect from receiver and remove all listeners."""
#     _LOG.debug("Disconnecting and removing all listeners")
#     await device.disconnect()
#     device.events.remove_all_listeners()


async def main():
    """Start the Remote Two integration driver."""

    logging.basicConfig(
        format=("%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-14s | %(message)s"), datefmt="%Y-%m-%d %H:%M:%S"
    )
    setup_logger()

    _LOG.debug("Starting driver...")
    await api.init("driver.json", driver_setup_handler)

    config.devices = config.Devices(api.config_dir_path, on_device_added, on_device_removed)
    for dv_info in config.devices:
        _configure_new_lyngdorf(dv_info, connect=False)


if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
