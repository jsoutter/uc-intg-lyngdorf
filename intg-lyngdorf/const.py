from enum import Enum
from typing import Any

from ucapi import media_player, remote

LYNGDORF_PORT = 84
LYNGDORF_SERVICE_TYPE = "_slactrl._tcp.local."


class EntityPrefix(str, Enum):
    """Enumeration of supported entities"""

    MEDIA_PLAYER = "media_player"
    REMOTE = "remote"
    # VOLUME = "volume"
    # MUTED = "muted"


class SimpleCommands(str, Enum):
    """Enumeration of supported remote command names for Lumagen control."""

    BACK = "back"
    DOWN = "down"
    EXIT = "exit"
    LEFT = "left"
    MENU = "menu"
    MUTE_TOGGLE = "mute toggle"
    NUM_0 = "0"
    NUM_1 = "1"
    NUM_2 = "2"
    NUM_3 = "3"
    NUM_4 = "4"
    NUM_5 = "5"
    NUM_6 = "6"
    NUM_7 = "7"
    NUM_8 = "8"
    NUM_9 = "9"
    OK = "ok"
    RIGHT = "right"
    SETUP = "setup"
    SRC_DOWN = "src down"
    SRC_UP = "src up"
    UP = "up"
    VOLUME_DOWN = "volume down"
    VOLUME_UP = "volume up"


class MediaPlayerDef:
    """
    Defines a media player entity including supported features, attributes, and
    a list of simple commands.
    """

    features = [
        media_player.Features.MUTE,
        media_player.Features.MUTE_TOGGLE,
        media_player.Features.SELECT_SOUND_MODE,
        media_player.Features.SELECT_SOURCE,
        media_player.Features.UNMUTE,
        media_player.Features.VOLUME,
        media_player.Features.VOLUME_UP_DOWN,
    ]
    attributes: dict[str, Any] = {
        media_player.Attributes.MUTED: False,
        media_player.Attributes.SOUND_MODE: "",
        media_player.Attributes.SOUND_MODE_LIST: [],
        media_player.Attributes.SOURCE: "",
        media_player.Attributes.SOURCE_LIST: [],
        media_player.Attributes.STATE: media_player.States.OFF,
        media_player.Attributes.VOLUME: None,
    }


class RemoteDef:
    """
    Defines a remote entity including supported features, attributes, and
    a list of simple commands.
    """

    features = [
        remote.Features.ON_OFF,
        remote.Features.TOGGLE,
        remote.Features.SEND_CMD,
    ]
    attributes: dict[str, Any] = {remote.Attributes.STATE: remote.States.UNKNOWN}
    simple_commands = [cmd.name for cmd in SimpleCommands]
