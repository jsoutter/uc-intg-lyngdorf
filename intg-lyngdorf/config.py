"""
Configuration handling of the integration driver.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import dataclasses
import json
import logging
import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any

from ucapi.entity import EntityTypes

_LOG = logging.getLogger(__name__)


def create_entity_id(device_id: str, entity_type: EntityTypes) -> str:
    """Create a unique entity identifier for the given receiver and entity type."""
    return f"{entity_type.value}.{device_id}"


def device_from_entity_id(entity_id: str) -> str | None:
    """
    Return the id prefix of an entity_id.

    :param entity_id: the entity identifier
    :return: the device prefix, or None if entity_id doesn't contain a dot
    """
    return entity_id.split(".", 1)[1]


class _EnhancedJSONEncoder(json.JSONEncoder):
    """Python dataclass JSON encoder."""

    def default(self, o: Any) -> Any:
        if dataclasses.is_dataclass(o):
            o = o  # runtime check ensures this is a dataclass
            return dataclasses.asdict(o)
        return super().default(o)


@dataclass
class LyngdorfConfigDevice:
    """Represents Lyngdorf device configuration including identity, network, and metadata."""

    identifier: str
    host: str
    port: str
    model: str

    def __repr__(self) -> str:
        return (
            f"<LyngdorfDeviceConfig id='{self.identifier}' host='{self.host}' port='{self.port}' model='{self.model}'>"
        )


class Devices:
    """Integration driver configuration class. Manages all configured Lyngdorf devices."""

    def __init__(
        self,
        data_path: str,
        add_handler: Callable[[LyngdorfConfigDevice], None],
        remove_handler: Callable[[LyngdorfConfigDevice | None], None],
        cfg_filename: str = "config.json",
    ) -> None:
        self._data_path: str = data_path
        self._cfg_file_path: str = os.path.join(data_path, cfg_filename)
        self._config: list[LyngdorfConfigDevice] = []
        self._add_handler = add_handler
        self._remove_handler = remove_handler
        self.load()

    def contains(self, device_id: str) -> bool:
        """Check if a device with the given ID exists in the configuration."""
        return any(d.identifier == device_id for d in self._config)

    def add(self, add: LyngdorfConfigDevice) -> None:
        """Add a new configured Lyngdorf device, ignoring duplicates by ID."""
        if any(d.identifier == add.identifier for d in self._config):
            _LOG.warning("Device with id '%s' already exists.", add.identifier)
            return
        self._config.append(add)
        if self._add_handler is not None:
            self._add_handler(add)
        self.store()
        _LOG.info("Device with id '%s' added and stored.", add.identifier)

    def remove(self, device_id: str) -> bool:
        """Remove a device from the configuration by its ID."""
        for i, device in enumerate(self._config):
            if device.identifier == device_id:
                removed_device = self._config.pop(i)
                if self._remove_handler is not None:
                    self._remove_handler(removed_device)
                self.store()
                _LOG.info("Device with id '%s' removed and changes stored.", device_id)
                return True
        _LOG.warning("Device with id '%s' not found for removal.", device_id)
        return False

    def get(self, device_id: str) -> LyngdorfConfigDevice | None:
        """Retrieve a device by ID, or None if not found."""
        for device in self._config:
            if device.identifier == device_id:
                return device
        return None

    def update(self, updated: LyngdorfConfigDevice) -> bool:
        """Update an existing device by matching ID. Returns True if updated."""
        for i, device in enumerate(self._config):
            if device.identifier == updated.identifier:
                self._config[i] = updated
                self.store()
                _LOG.info("Device with id '%s' was updated and stored.", updated.identifier)
                return True
        _LOG.warning("Device with id '%s' not found for update.", updated.identifier)
        return False

    def clear(self) -> None:
        """Remove all device configurations and delete the configuration file."""
        self._config.clear()

        if os.path.exists(self._cfg_file_path):
            os.remove(self._cfg_file_path)

        if self._remove_handler is not None:
            self._remove_handler(None)
        _LOG.info("All devices cleared and config file removed.")

    def load(self) -> bool:
        """
        Load the config into the internal list.

        :return: True if the configuration could be loaded.
        """
        try:
            with open(self._cfg_file_path, encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                if not all(k in item for k in ("identifier", "host", "port", "model")):
                    _LOG.warning("Skipping invalid config item: %s", item)
                    continue
                try:
                    lyngdorf = LyngdorfConfigDevice(**item)
                except TypeError as e:
                    _LOG.warning("Invalid device format: %s (%s)", item, e)
                    continue
                self._config.append(lyngdorf)
            return True

        except FileNotFoundError:
            _LOG.info(
                "No config file found at %s. Starting with an empty configuration.",
                self._cfg_file_path,
            )
        except JSONDecodeError:
            _LOG.error("Config file is present but contains invalid JSON.")
        except OSError:
            _LOG.exception("Cannot open the config file")
        except ValueError:
            _LOG.exception("Empty or invalid config file")

        return False

    def store(self) -> bool:
        """
        Store the configuration file.

        :return: True if the configuration could be saved.
        """
        try:
            with open(self._cfg_file_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, cls=_EnhancedJSONEncoder)
            return True
        except OSError:
            _LOG.exception("Cannot write the config file")

        return False

    def __iter__(self) -> Iterator[LyngdorfConfigDevice]:
        """Allow iteration directly on the Devices instance."""
        return iter(self._config)


devices: Devices | None = None
