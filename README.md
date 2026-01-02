# Lyngdorf Integration for Unfolded Circle Remotes

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

## ⚠️ Disclaimer ⚠️

This software may contain bugs that could affect system stability. Please use it at your own risk!

This integration driver allows control of a Lyngdorf devices, it uses the 
[uc-integration-api](https://github.com/aitatoi/integration-python-library) and [UCAPI Framework](https://github.com/JackJPowell/ucapi-framework) libraries to communicate with the Remote Two/3.

Entities:
- [Media Player](https://github.com/unfoldedcircle/core-api/blob/main/doc/entities/entity_media_player.md)
- [Remote](https://github.com/unfoldedcircle/core-api/blob/main/doc/entities/entity_remote.md)
- [Sensor](https://github.com/unfoldedcircle/core-api/blob/main/doc/entities/entity_sensor.md)

Supported devices:
- MP-40, MP-50, MP-60, TDAI-1120, TDAI-2210 and TDAI-3400.

Media Player attributes:

| | MP-40, MP-50, MP-60 | TDAI-1120, TDAI-2210, TDAI-3400 |
|-|-|-|
| State (on, off) | ✅ | ✅ |
| Source List | ✅ | ✅ |
| Sound Modes | ✅ | ❌ |

Media Player commands:

| | MP-40, MP-50, MP-60 | TDAI-1120, TDAI-2210, TDAI-3400 |
|-|-|-|
| Turn on & off | ✅ | ✅ |
| Volume up / down | ✅ | ✅ |
| Mute, unmute and mute toggle | ✅ | ✅ |
| Play, next and previous | ✅ | ✅ |
| Directional pad navigation and select | ✅ | ❌ |
| Numeric digits | ✅ | ❌ |
| Menu, info, settings and back | ✅ | ❌ |

Sensors:

| Name | Units | MP-40, MP-50, MP-60 | TDAI-1120, TDAI-2210, TDAI-3400 |
|-|-|-|-|
| Source | | ✅ | ✅ |
| Volume | dB | ✅ | ✅ |
| Stream type | | ✅ | ✅ |
| Voicing | | ✅ | ✅ |
| Focus position | | ✅ | ✅ |
| Audio input | | ✅ | ❌ |
| Audio type | | ✅ | ✅ |
| Video input | | ✅ | ❌ |
| Video type | | ✅ | ❌ |
| Video output | | ✅ | ❌ |
| Lipsync | ms | ✅ | ❌ |
| Bass trim | dB | ✅ | ❌ |
| Treble trim | dB | ✅ | ❌ |
| Center trim | dB | ✅ | ❌ |
| Heights trim | dB | ✅ | ❌ |
| LFE trim | dB | ✅ | ❌ |
| Surrounds trim | dB | ✅ | ❌ |

Remote Commands:

| Command | MP-40, MP-50, MP-60 | TDAI-1120, TDAI-2210, TDAI-3400 |
|-|-|-|
| volume_up | ✅ | ✅ |
| volume_down | ✅ | ✅ |
| mute_toggle | ✅ | ✅ |
| mute | ✅ | ✅ |
| unmute | ✅ | ✅ |
| play_pause | ✅ | ✅ |
| next | ✅ | ✅ |
| previous | ✅ | ✅ |
| SOURCE_BUTTON | ✅ | ❌ |
| SOURCE_NEXT | ✅ | ✅ |
| SOURCE_PREV | ✅ | ✅ |
| VOICING_NEXT | ✅ | ✅ |
| VOICING_PREV | ✅ | ✅ |
| FOCUS_POSITION_NEXT | ✅ | ✅ |
| FOCUS_POSITION_PREV | ✅ | ✅ |
| cursor_up | ✅ | ❌ |
| cursor_down | ✅ | ❌ |
| cursor_left | ✅ | ❌ |
| cursor_right | ✅ | ❌ |
| cursor_enter | ✅ | ❌ |
| digit_0 | ✅ | ❌ |
| digit_1 | ✅ | ❌ |
| digit_2 | ✅ | ❌ |
| digit_3 | ✅ | ❌ |
| digit_4 | ✅ | ❌ |
| digit_5 | ✅ | ❌ |
| digit_6 | ✅ | ❌ |
| digit_7 | ✅ | ❌ |
| digit_8 | ✅ | ❌ |
| digit_9 | ✅ | ❌ |
| menu | ✅ | ❌ |
| info | ✅ | ❌ |
| settings | ✅ | ❌ |
| back | ✅ | ❌ |
| AUDIO_MODE_BUTTON | ✅ | ❌ |
| AUDIO_MODE_NEXT | ✅ | ❌ |
| AUDIO_MODE_PREV | ✅ | ❌ |
| LIPSYNC_UP | ✅ | ❌ |
| LIPSYNC_DOWN | ✅ | ❌ |
| DTS_DIALOG_UP | ✅ | ❌ |
| DTS_DIALOG_DOWN | ✅ | ❌ |
| BASS_TRIM_UP | ✅ | ❌ |
| BASS_TRIM_DOWN | ✅ | ❌ |
| TREBLE_TRIM_UP | ✅ | ❌ |
| TREBLE_TRIM_DOWN | ✅ | ❌ |
| CENTER_TRIM_UP | ✅ | ❌ |
| CENTER_TRIM_DOWN | ✅ | ❌ |
| HEIGHTS_TRIM_UP | ✅ | ❌ |
| HEIGHTS_TRIM_DOWN | ✅ | ❌ |
| LFE_TRIM_UP | ✅ | ❌ |
| LFE_TRIM_DOWN | ✅ | ❌ |
| SURROUNDS_TRIM_UP | ✅ | ❌ |
| SURROUNDS_TRIM_DOWN | ✅ | ❌ |

### Network

- The Lyngdorf device must be on the same network subnet as the Remote. 
- When using DHCP a static IP address reservation for the Lyngdorf device(s) is recommended.
- Bonjour discovery is used to detect Lyngdorf devices on the network.

## Usage

### Install on Remote

- Download tar.gz file from Releases section of this repository.
- Upload the file to the remove via the integrations tab (Requires Remote Beta).

## Versioning

[SemVer](http://semver.org/) is used for versioning. For the versions available, see the [tags and releases in this repository](https://github.com/jsoutter/uc-intg-lyngdorf/releases).

## Changelog

The major changes found in each new release are listed under the GitHub [releases](https://github.com/jsoutter/uc-intg-lyngdorf/releases).

## License

This project is licensed under the [**Mozilla Public License 2.0**](https://choosealicense.com/licenses/mpl-2.0/).
See the [LICENSE](LICENSE) file for details.