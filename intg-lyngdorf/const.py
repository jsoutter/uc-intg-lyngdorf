"""
This module implements constants for the Lyngdorf integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pylyngdorf.const import LyngdorfQuery
from pylyngdorf.lyngdorf import Lyngdorf

LYNGDORF_SERVICE_TYPE = "_slactrl._tcp.local."
DEFAULT_DB_VALUE = "--.-"


def format_db(value: float | None) -> str | None:
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


# class SimpleCommands(str, Enum):
#     """Enumeration of supported remote command names for Lyngdorf control."""

#     BACK = "back"
#     MUTE_TOGGLE = "mute toggle"
#     UP = "up"
#     DOWN = "down"
#     ENTER = "ok"
#     LEFT = "left"
#     RIGHT = "right"
#     DIGIT_0 = "0"
#     DIGIT_1 = "1"
#     DIGIT_2 = "2"
#     DIGIT_3 = "3"
#     DIGIT_4 = "4"
#     DIGIT_5 = "5"
#     DIGIT_6 = "6"
#     DIGIT_7 = "7"
#     DIGIT_8 = "8"
#     DIGIT_9 = "9"
#     EXIT = "exit"
#     MENU = "menu"
#     SETUP = "setup"
#     SRC_DOWN = "src down"
#     SRC_UP = "src up"
#     VOLUME_DOWN = "volume down"
#     VOLUME_UP = "volume up"
