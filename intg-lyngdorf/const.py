"""Lyngdorf device integration constants."""

from enum import Enum
from typing import Any

from ucapi import media_player, remote

LYNGDORF_SERVICE_TYPE = "_slactrl._tcp.local."


class EntityPrefix(str, Enum):
    """Enumeration of supported entities"""

    MEDIA_PLAYER = "media_player"
    REMOTE = "remote"


class SensorEntityPrefix(str, Enum):
    """Enumeration of supported sensor entities"""

    VOLUME = "volume"
    STREAM_TYPE = "stream_type"
    VOICING = "voicing"
    FOCUS_POSITION = "focus_position"
    AUDIO_INPUT = "audio_input"
    AUDIO_TYPE = "audio_type"
    VIDEO_INPUT = "video_input"
    VIDEO_TYPE = "video_type"
    VIDEO_OUTPUT = "video_output"
    LIPSYNC = "lipsync"
    BASS_TRIM = "bass_trim"
    TREBLE_TRIM = "treble_trim"
    CENTER_TRIM = "center_trim"
    HEIGHTS_TRIM = "heights_trim"
    LFE_TRIM = "lfe_trim"
    SURROUNDS_TRIM = "surrounds_trim"


class SimpleCommands(str, Enum):
    """Enumeration of supported remote command names for Lyngdorf control."""

    BACK = "back"
    MUTE_TOGGLE = "mute toggle"
    UP = "up"
    DOWN = "down"
    ENTER = "ok"
    LEFT = "left"
    RIGHT = "right"
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
        media_player.Features.ON_OFF,
        media_player.Features.VOLUME,
        media_player.Features.VOLUME_UP_DOWN,
        media_player.Features.MUTE_TOGGLE,
        media_player.Features.MUTE,
        media_player.Features.UNMUTE,
        media_player.Features.PLAY_PAUSE,
        media_player.Features.NEXT,
        media_player.Features.PREVIOUS,
        media_player.Features.SELECT_SOURCE,
        # MP devices only
        media_player.Features.SELECT_SOUND_MODE,
        media_player.Features.DPAD,
        media_player.Features.NUMPAD,
        media_player.Features.HOME,
        media_player.Features.MENU,
        media_player.Features.INFO,
        media_player.Features.SETTINGS,
    ]
    attributes: dict[str, Any] = {
        media_player.Attributes.MUTED: False,
        media_player.Attributes.SOURCE: "",
        media_player.Attributes.SOURCE_LIST: [],
        media_player.Attributes.STATE: media_player.States.OFF,
        media_player.Attributes.VOLUME: None,
        # MP devices only
        media_player.Attributes.SOUND_MODE: "",
        media_player.Attributes.SOUND_MODE_LIST: [],
    }


class RemoteDef:
    """
    Defines a remote entity including supported features, attributes, and
    a list of simple commands.
    """

    features = [
        remote.Features.SEND_CMD,
        remote.Features.ON_OFF,
    ]
    attributes: dict[str, Any] = {remote.Attributes.STATE: remote.States.UNKNOWN}
    simple_commands = [cmd.name for cmd in SimpleCommands]
