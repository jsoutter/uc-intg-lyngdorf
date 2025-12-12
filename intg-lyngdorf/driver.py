"""
This module implements a Remote Two/3 integration driver for Lyngdorf devices.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

import ucapi
from pylyngdorf.const import DeviceModel
from pylyngdorf.lyngdorf import Lyngdorf
from ucapi.entity import Entity
from ucapi.media_player import Attributes as MediaAttr
from ucapi.media_player import States
from ucapi.sensor import Attributes as SensorAttr

import config
from api import api, loop
from config import LyngdorfDeviceConfig, device_from_entity_id
from const import SensorEntityPrefix
from media_player import LyngdorfMediaPlayer
from registry import (
    all_devices,
    clear_devices,
    connect_all,
    disconnect_all,
    get_device,
    iter_devices,
    register_device,
    unregister_device,
)
from remote import REMOTE_STATE_MAPPING, LyngdorfRemote
from sensor import LyngdorfSensor
from setup_flow import driver_setup_handler
from utils import setup_logger

_LOG = logging.getLogger("driver")


@api.listens_to(ucapi.Events.CONNECT)  # type: ignore[reportUnknownMemberType]
async def on_connect() -> None:
    """Connect all configured receivers when the Remote Two sends the connect command."""
    _LOG.info("Received connect event message from remote")
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)
    loop.create_task(connect_all())


@api.listens_to(ucapi.Events.DISCONNECT)  # type: ignore[reportUnknownMemberType]
async def on_r2_disconnect() -> None:
    """Disconnect notification from the Remote Two."""
    _LOG.info("Received disconnect event message from remote")
    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)
    loop.create_task(disconnect_all())


@api.listens_to(ucapi.Events.ENTER_STANDBY)  # type: ignore[reportUnknownMemberType]
async def on_r2_enter_standby() -> None:
    """
    Enter standby notification from Remote Two.

    Disconnect every Lyngdorf instance.
    """
    _LOG.debug("Enter standby event: disconnecting device(s)")
    loop.create_task(disconnect_all())


@api.listens_to(ucapi.Events.EXIT_STANDBY)  # type: ignore[reportUnknownMemberType]
async def on_r2_exit_standby() -> None:
    """
    Exit standby notification from Remote Two.

    Connect all Lyngdorf instances.
    """
    _LOG.debug("Exit standby event: connecting device(s)")
    loop.create_task(connect_all())


@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)  # type: ignore[reportUnknownMemberType]
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """
    _LOG.debug("Subscribe entities event: %s", entity_ids)

    for entity_id in entity_ids:
        device_id = device_from_entity_id(entity_id)
        if device_id is not None:
            if device_id in all_devices():
                if (configured_entity := api.configured_entities.get(entity_id)) is None:
                    _LOG.debug("Device connected: entity %s is not configured, ignoring", entity_id)
                    continue

                """
                device = get_device(device_id)
                _update_entity_attributes(entity_id, configured_entity, device.attributes)
                """
                _update_entity_attributes(entity_id, configured_entity, {})
                continue

            device_config = config.devices.get(device_id) if config.devices else None
            if device_config:
                _add_configured_device(device_config, True)
            else:
                _LOG.error(
                    "Failed to subscribe entity %s: no Lygndorf instance found",
                    entity_id,
                )


def _update_entity_attributes(entity_id: str, entity: Entity, attributes: dict[str, Any]):
    """
    Update attributes for the given entity based on its type.
    """
    if isinstance(entity, LyngdorfMediaPlayer):
        api.configured_entities.update_attributes(entity_id, attributes)

    elif isinstance(entity, LyngdorfRemote):
        api.configured_entities.update_attributes(
            entity_id,
            {ucapi.remote.Attributes.STATE: REMOTE_STATE_MAPPING.get(attributes.get(MediaAttr.STATE, States.UNKNOWN))},
        )
    elif isinstance(entity, LyngdorfSensor):
        pass


@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)  # type: ignore[reportUnknownMemberType]
async def on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """On unsubscribe, we disconnect the objects."""
    _LOG.debug("Unsubscribe entities event: %s", entity_ids)

    # Collect devices associated with the entities being unsubscribed
    devices_to_remove: set[str] = set()
    for entity_id in entity_ids:
        device_id = device_from_entity_id(entity_id)
        if device_id is None:
            continue
        devices_to_remove.add(device_id)

    # Check other remaining entities to see if they still use these devices
    remaining_entities = [e for e in api.configured_entities.get_all() if e.get("entity_id") not in entity_ids]

    for entity_id in remaining_entities:
        device_id = config.device_from_entity_id(str(entity_id))
        if device_id:
            devices_to_remove.discard(device_id)

    # Disconnect and clean up devices no longer in use
    for device_id in devices_to_remove:
        if device_id in all_devices():
            if device := get_device(device_id):
                await device.async_disconnect()
                # TODO device.events.remove_all_listeners()


def _add_configured_device(device_config: LyngdorfDeviceConfig, connect: bool = False) -> None:
    """
    Create and configure a new Lyngdorf device.

    If a device already exists for the given device ID, reuse it.
    Otherwise, create and register a new one.

    :param info: The Lyngdorf device configuration.
    :param connect: Whether to initiate connection immediately.
    """
    device: Lyngdorf | None = get_device(device_config.identifier)

    if device:

        async def start_disconnection():
            await device.async_disconnect()

        loop.create_task(start_disconnection())
    else:
        model: DeviceModel
        try:
            model = DeviceModel(device_config.model)
        except ValueError:
            model = DeviceModel.MP60

        # Create wrapper and add events for LyngdorfDevice class
        device = Lyngdorf.create(device_config.host, device_config.port, device_model=model)

        register_device(device_config.identifier, device)
        _LOG.debug("Registered device: %s:%s (%s)", device_config.host, device_config.port, device_config.model)

    async def start_connection():
        await device.async_connect()

    if connect:
        loop.create_task(start_connection())

    _register_available_entities(device_config, device)


def _register_available_entities(config: LyngdorfDeviceConfig, device: Lyngdorf) -> None:
    """
    Register remote and media player entities.

    :param info: LyngdorfDevice configuration
    :param device: Active Lyngdorf for the device
    """
    for entity_cls in (LyngdorfRemote, LyngdorfMediaPlayer):
        entity = entity_cls(config, device)
        if api.available_entities.contains(entity.id):
            api.available_entities.remove(entity.id)
        api.available_entities.add(entity)

    for sensor in SensorEntityPrefix:  # Add additional field for confugurign sensor (As per HA)
        entity = LyngdorfSensor(config, sensor.value)
        if api.available_entities.contains(entity.id):
            api.available_entities.remove(entity.id)
        api.available_entities.add(entity)


# def _device_state_to_media_player_state(device_state: bool) -> States:
#     if device_state

#     match device_state:
#         case tv.PowerState.ON:
#             state = States.ON
#         case tv.PowerState.STANDBY:
#             state = States.STANDBY
#         case tv.PowerState.OFF:
#             state = States.OFF
#         case _:
#             state = States.UNKNOWN
#     return state


# async def on_update(entity_id: str, update: dict[str, Any] | None) -> None:
#     """
#     Update attributes of configured media-player or remote entity if device attributes changed.

#     :param device_id: Device identifier.
#     :param update: Dictionary containing the updated attributes or None.
#     """
#     if update is None:
#         return

#     device_id = entity_id.split(".", 1)[1]
#     device = get_device(device_id)
#     if device is None:
#         return

#     _LOG.debug("[%s] Update............: %s", entity_id, update)

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


def on_device_added(device_config: LyngdorfDeviceConfig) -> None:
    """Handle a newly added device in the configuration."""
    _LOG.debug("New device added: %s", device_config)
    _add_configured_device(device_config, connect=False)


def on_device_removed(device_config: LyngdorfDeviceConfig | None) -> None:
    """Handle a removed device in the configuration."""
    if device_config is None:
        _LOG.debug("Configuration cleared, disconnecting & removing all configured device instances")
        for configured in iter_devices():
            loop.create_task(_async_remove(configured))
            # TODO device.events.remove_all_listeners()

        clear_devices()
        api.configured_entities.clear()
        api.available_entities.clear()
    else:
        device = get_device(device_config.identifier)
        if device:
            _LOG.debug("Disconnecting from removed device %s", device_config.identifier)
            unregister_device(device_config.identifier)
            loop.create_task(_async_remove(device))
            # TODO device.events.remove_all_listeners()

            # TODO Determine list of entities media_player, remote and sensors
            # get_device id
            # entities = [e for e in api.configured_entities.get_all() if e.get("entity_id") not in entity_ids]
            entity_id = device_config.identifier
            api.configured_entities.remove(entity_id)
            api.available_entities.remove(entity_id)


async def _async_remove(device: Lyngdorf) -> None:
    """Disconnect from receiver and remove all listeners."""
    await device.async_disconnect()


async def main():
    """Start the Remote Two integration driver."""

    logging.basicConfig(
        format=("%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-14s | %(message)s"),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    setup_logger()

    _LOG.debug("Starting driver...")
    await api.init("driver.json", driver_setup_handler)

    config.devices = config.Devices(api.config_dir_path, on_device_added, on_device_removed)

    for device_config in config.devices:
        _add_configured_device(device_config)


if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
