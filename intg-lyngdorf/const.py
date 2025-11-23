from enum import Enum
from typing import Any

from ucapi import media_player, remote

LYNGDORF_PORT = 84
LYNGDORF_SERVICE_TYPE = "_slactrl._tcp.local."


class SensorEntityPrefix(str, Enum):
    """Enumeration of supported entities"""

    VOLUME = "volume"


class SimpleCommands(str, Enum):
    """Enumeration of supported remote command names for Lyngdorf control."""

    BACK = "back"
    MUTE_TOGGLE = "mute toggle"
    CURSOR_DOWN = "down"
    CURSOR_ENTER = "ok"
    CURSOR_LEFT = "left"
    CURSOR_RIGHT = "right"
    CURSOR_UP = "up"
    DIGIT_0 = "0"
    DIGIT_1 = "1"
    DIGIT_2 = "2"
    DIGIT_3 = "3"
    DIGIT_4 = "4"
    DIGIT_5 = "5"
    DIGIT_6 = "6"
    DIGIT_7 = "7"
    DIGIT_8 = "8"
    DIGIT_9 = "9"
    EXIT = "exit"
    MENU = "menu"
    SETUP = "setup"
    SRC_DOWN = "src down"
    SRC_UP = "src up"
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
        remote.Features.SEND_CMD,
        remote.Features.ON_OFF,
        remote.Features.TOGGLE,
    ]
    attributes: dict[str, Any] = {remote.Attributes.STATE: remote.States.UNKNOWN}
    simple_commands = [cmd.name for cmd in SimpleCommands]
