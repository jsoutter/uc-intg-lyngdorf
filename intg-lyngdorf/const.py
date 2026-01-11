"""
This module implements constants for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any

from pylyngdorf.const import LyngdorfCommand, LyngdorfQuery
from pylyngdorf.lyngdorf import Lyngdorf
from ucapi import media_player

LYNGDORF_SERVICE_TYPE = "_slactrl._tcp.local."
DEFAULT_DB_VALUE = "--.-"


def format_db(value: float | None) -> str | None:
    """Format value to one decimal place."""
    return None if value is None else f"{value:.1f}"


@dataclass
class LyngdorfConfig:
    """Lyngdorf device configuration."""

    identifier: str
    name: str
    address: str
    port: int
    model: str
    multichannel: bool


@dataclass(frozen=True, kw_only=True)
class LyngdorfSensorConfig:
    """Class to describe an Lyngdorf sensor entity."""

    identifier: str
    name: str
    unit_of_measurement: str | None = None
    options: dict[str, Any] | None = None
    default_value: str = ""
    multichannel: bool = False
    event: LyngdorfQuery
    value_fn: Callable[[Lyngdorf], str | int | float | None]


SENSOR_TYPES: tuple[LyngdorfSensorConfig, ...] = (
    LyngdorfSensorConfig(
        identifier="source",
        name="Source",
        event=LyngdorfQuery.SOURCE,
        value_fn=lambda receiver: receiver.source,
    ),
    LyngdorfSensorConfig(
        identifier="volume",
        name="Volume",
        unit_of_measurement="dB",
        default_value=DEFAULT_DB_VALUE,
        event=LyngdorfQuery.VOLUME,
        value_fn=lambda receiver: format_db(receiver.volume),
    ),
    LyngdorfSensorConfig(
        identifier="stream_type",
        name="Stream type",
        event=LyngdorfQuery.STREAM_TYPE,
        default_value="n/a",
        value_fn=lambda receiver: receiver.stream_type,
    ),
    LyngdorfSensorConfig(
        identifier="voicing",
        name="Voicing",
        event=LyngdorfQuery.VOICING,
        value_fn=lambda receiver: receiver.voicing,
    ),
    LyngdorfSensorConfig(
        identifier="focus_position",
        name="Focus position",
        event=LyngdorfQuery.FOCUS_POSITION,
        value_fn=lambda receiver: receiver.focus_position,
    ),
    LyngdorfSensorConfig(
        identifier="audio_input",
        name="Audio input",
        multichannel=True,
        event=LyngdorfQuery.AUDIO_INPUT,
        value_fn=lambda receiver: receiver.audio_input,
    ),
    LyngdorfSensorConfig(
        identifier="audio_type",
        name="Audio type",
        event=LyngdorfQuery.AUDIO_TYPE,
        value_fn=lambda receiver: receiver.audio_type,
    ),
    LyngdorfSensorConfig(
        identifier="video_input",
        name="Video input",
        multichannel=True,
        event=LyngdorfQuery.VIDEO_INPUT,
        value_fn=lambda receiver: receiver.video_input,
    ),
    LyngdorfSensorConfig(
        identifier="video_type",
        name="Video type",
        multichannel=True,
        event=LyngdorfQuery.VIDEO_TYPE,
        value_fn=lambda receiver: receiver.video_type,
    ),
    LyngdorfSensorConfig(
        identifier="video_output",
        name="Video output",
        multichannel=True,
        event=LyngdorfQuery.VIDEO_OUTPUT,
        value_fn=lambda receiver: receiver.video_output,
    ),
    LyngdorfSensorConfig(
        identifier="lipsync",
        name="Lipsync",
        unit_of_measurement="ms",
        default_value="---",
        multichannel=True,
        event=LyngdorfQuery.LIPSYNC,
        value_fn=lambda receiver: str(receiver.lipsync),
    ),
    LyngdorfSensorConfig(
        identifier="bass_trim",
        name="Bass trim",
        unit_of_measurement="dB",
        default_value=DEFAULT_DB_VALUE,
        multichannel=True,
        event=LyngdorfQuery.BASS_TRIM,
        value_fn=lambda receiver: format_db(receiver.bass_trim),
    ),
    LyngdorfSensorConfig(
        identifier="treble_trim",
        name="Treble trim",
        unit_of_measurement="dB",
        default_value=DEFAULT_DB_VALUE,
        multichannel=True,
        event=LyngdorfQuery.TREBLE_TRIM,
        value_fn=lambda receiver: format_db(receiver.treble_trim),
    ),
    LyngdorfSensorConfig(
        identifier="center_trim",
        name="Center trim",
        unit_of_measurement="dB",
        default_value=DEFAULT_DB_VALUE,
        multichannel=True,
        event=LyngdorfQuery.CENTER_TRIM,
        value_fn=lambda receiver: format_db(receiver.center_trim),
    ),
    LyngdorfSensorConfig(
        identifier="heights_trim",
        name="Heights trim",
        unit_of_measurement="dB",
        default_value=DEFAULT_DB_VALUE,
        multichannel=True,
        event=LyngdorfQuery.HEIGHTS_TRIM,
        value_fn=lambda receiver: format_db(receiver.heights_trim),
    ),
    LyngdorfSensorConfig(
        identifier="lfe_trim",
        name="LFE trim",
        unit_of_measurement="dB",
        default_value=DEFAULT_DB_VALUE,
        multichannel=True,
        event=LyngdorfQuery.LFE_TRIM,
        value_fn=lambda receiver: format_db(receiver.lfe_trim),
    ),
    LyngdorfSensorConfig(
        identifier="surrounds_trim",
        name="Surrounds trim",
        unit_of_measurement="dB",
        default_value=DEFAULT_DB_VALUE,
        multichannel=True,
        event=LyngdorfQuery.SURROUNDS_TRIM,
        value_fn=lambda receiver: format_db(receiver.surrounds_trim),
    ),
)


class SimpleCommands(str, Enum):
    """Common simple commands not covered by media-player features."""

    SOURCE_NEXT = "SOURCE_NEXT"
    SOURCE_PREV = "SOURCE_PREV"
    VOICING_NEXT = "VOICING_NEXT"
    VOICING_PREV = "VOICING_PREV"
    FOCUS_POSITION_NEXT = "FOCUS_POSITION_NEXT"
    FOCUS_POSITION_PREV = "FOCUS_POSITION_PREV"


SIMPLE_COMMANDS_MAP = MappingProxyType(
    {
        SimpleCommands.SOURCE_NEXT.value: LyngdorfCommand.SOURCE_NEXT,
        SimpleCommands.SOURCE_PREV.value: LyngdorfCommand.SOURCE_PREV,
        SimpleCommands.VOICING_NEXT.value: LyngdorfCommand.VOICING_NEXT,
        SimpleCommands.VOICING_PREV.value: LyngdorfCommand.VOICING_PREV,
        SimpleCommands.FOCUS_POSITION_NEXT.value: LyngdorfCommand.FOCUS_POSITION_NEXT,
        SimpleCommands.FOCUS_POSITION_PREV.value: LyngdorfCommand.FOCUS_POSITION_PREV,
    }
)


MULTICHANNEL_SIMPLE_COMMANDS_MAP = MappingProxyType(
    {
        "SOURCE_BUTTON": LyngdorfCommand.SOURCE_BUTTON,
        "AUDIO_MODE_BUTTON": LyngdorfCommand.AUDIO_MODE_BUTTON,
        "AUDIO_MODE_NEXT": LyngdorfCommand.AUDIO_MODE_NEXT,
        "AUDIO_MODE_PREV": LyngdorfCommand.AUDIO_MODE_PREV,
        "LIPSYNC_UP": LyngdorfCommand.LIPSYNC_UP,
        "LIPSYNC_DOWN": LyngdorfCommand.LIPSYNC_DOWN,
        "DTS_DIALOG_UP": LyngdorfCommand.DTS_DIALOG_UP,
        "DTS_DIALOG_DOWN": LyngdorfCommand.DTS_DIALOG_DOWN,
        "BASS_TRIM_UP": LyngdorfCommand.BASS_TRIM_UP,
        "BASS_TRIM_DOWN": LyngdorfCommand.BASS_TRIM_DOWN,
        "TREBLE_TRIM_UP": LyngdorfCommand.TREBLE_TRIM_UP,
        "TREBLE_TRIM_DOWN": LyngdorfCommand.TREBLE_TRIM_DOWN,
        "CENTER_TRIM_UP": LyngdorfCommand.CENTER_TRIM_UP,
        "CENTER_TRIM_DOWN": LyngdorfCommand.CENTER_TRIM_DOWN,
        "HEIGHTS_TRIM_UP": LyngdorfCommand.HEIGHTS_TRIM_UP,
        "HEIGHTS_TRIM_DOWN": LyngdorfCommand.HEIGHTS_TRIM_DOWN,
        "LFE_TRIM_UP": LyngdorfCommand.LFE_TRIM_UP,
        "LFE_TRIM_DOWN": LyngdorfCommand.LFE_TRIM_DOWN,
        "SURROUNDS_TRIM_UP": LyngdorfCommand.SURROUNDS_TRIM_UP,
        "SURROUNDS_TRIM_DOWN": LyngdorfCommand.SURROUNDS_TRIM_DOWN,
    }
)

MULTICHANNEL_MEDIA_PLAYER_COMMANDS_MAP = MappingProxyType(
    {
        media_player.Commands.CURSOR_UP.value: LyngdorfCommand.CURSOR_UP,
        media_player.Commands.CURSOR_DOWN.value: LyngdorfCommand.CURSOR_DOWN,
        media_player.Commands.CURSOR_LEFT.value: LyngdorfCommand.CURSOR_LEFT,
        media_player.Commands.CURSOR_RIGHT.value: LyngdorfCommand.CURSOR_RIGHT,
        media_player.Commands.CURSOR_ENTER.value: LyngdorfCommand.CURSOR_ENTER,
        media_player.Commands.DIGIT_0.value: LyngdorfCommand.DIGIT_0,
        media_player.Commands.DIGIT_1.value: LyngdorfCommand.DIGIT_1,
        media_player.Commands.DIGIT_2.value: LyngdorfCommand.DIGIT_2,
        media_player.Commands.DIGIT_3.value: LyngdorfCommand.DIGIT_3,
        media_player.Commands.DIGIT_4.value: LyngdorfCommand.DIGIT_4,
        media_player.Commands.DIGIT_5.value: LyngdorfCommand.DIGIT_5,
        media_player.Commands.DIGIT_6.value: LyngdorfCommand.DIGIT_6,
        media_player.Commands.DIGIT_7.value: LyngdorfCommand.DIGIT_7,
        media_player.Commands.DIGIT_8.value: LyngdorfCommand.DIGIT_8,
        media_player.Commands.DIGIT_9.value: LyngdorfCommand.DIGIT_9,
        media_player.Commands.MENU.value: LyngdorfCommand.MENU,
        media_player.Commands.INFO.value: LyngdorfCommand.INFO,
        media_player.Commands.SETTINGS.value: LyngdorfCommand.SETTINGS,
        media_player.Commands.BACK.value: LyngdorfCommand.BACK,
    }
)
