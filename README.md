# smartmonitor-hid

[![Tests](https://img.shields.io/badge/tests-16%20passing-brightgreen)](./tests)
[![License](https://img.shields.io/badge/license-GPL--3.0--or--later-blue.svg)](./LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](./CHANGELOG.md)

Standalone Python library for 3.5" SmartMonitor HID displays on Linux.

`smartmonitor-hid` is intended for projects that need to:

- detect a SmartMonitor HID display
- upload a compiled `img.dat` / `.dat` theme
- send runtime metric values and current time
- inspect vendor `.ui` themes
- compile `.ui` themes into device-ready `img.dat`

This library exists to keep the SmartMonitor HID protocol and theme workflow
separate from bitmap-driven monitor applications.

Active repository:
- https://github.com/Agentry433/smartmonitor_hid_lib

## Features

- HID auto-detection via `hidraw`
- SmartMonitor reset / YMODEM theme upload
- runtime metric packet sender
- datetime packet sender
- runtime tag mapping helpers
- standalone `.ui` parser / writer
- standalone `.img.dat` parser / record packer
- standalone `.ui -> img.dat` compiler
- CLI entry point: `smartmonitor-hid`
- pure Python test suite for the non-hardware parts

## Requirements

- Python `3.11+`
- Linux with access to `/dev/hidraw*`
- `Pillow`
- `fc-match` is recommended for the compiler text rendering path

## Installation

### From a local checkout

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install .
```

### Editable install for development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Quick Start

### Detect the monitor

```bash
smartmonitor-hid detect
```

### Upload a theme

```bash
smartmonitor-hid upload-theme path/to/img.dat
```

### Send current date and time

```bash
smartmonitor-hid send-time
```

### Inspect a vendor `.ui`

```bash
smartmonitor-hid inspect-ui theme.ui
```

### Compile a `.ui` theme

```bash
smartmonitor-hid compile-ui theme.ui output.dat
```

## Python Example

```python
from pathlib import Path

from smartmonitor_hid import (
    SmartMonitorClient,
    ThemeSensorSpec,
    ThemeWidgetSpec,
)

with SmartMonitorClient.auto() as client:
    client.upload_theme(Path("img.dat"))
    client.send_datetime()

    widgets = [
        ThemeWidgetSpec(
            object_name="cpu_temp",
            widget_type=5,
            sensor=ThemeSensorSpec(
                fast_sensor=1,
                sensor_type_name="Temperature",
                sensor_name="CPU Package",
                reading_name="CPU Temperature",
            ),
        ),
    ]

    mapping = client.build_theme_tag_mapping(widgets)
    client.send_runtime_metrics(mapping, {"CPU_TEMP": 42})
```

## Command Line Interface

```bash
smartmonitor-hid detect
smartmonitor-hid upload-theme img.dat
smartmonitor-hid send-time
smartmonitor-hid inspect-ui theme.ui
smartmonitor-hid inspect-imgdat img.dat
smartmonitor-hid compile-ui theme.ui output.dat
smartmonitor-hid map-ui theme.ui
```

You can also run it as a module:

```bash
python -m smartmonitor_hid detect
```

## Bridge Configuration

The package is already standalone for transport, runtime, `.ui`, `.img.dat`,
and compile flows.

An optional bridge layer still exists for cases where you want to import extra
host-project modules from another repository. For that, use:

```bash
export SMARTMONITOR_HID_PROJECT_ROOT=/path/to/project
```

or:

```python
from smartmonitor_hid import configure_project_root

configure_project_root("/path/to/project")
```

## Documentation

- [MANUAL.md](MANUAL.md) - full usage and integration guide
- [README_RU.md](README_RU.md) - Russian overview
- [MANUAL_RU.md](MANUAL_RU.md) - Russian usage and integration guide

## Support the Project

If you find this project useful, you can support the development with a donation:

TON Wallet:

`UQAnWldcIWfwKUmnJN5kMqW5VY6SuVwTtrnRpDEE_rilh8Qj`

Bitcoin (BTC):

`bc1qelwv8jm2j9pughk5rte0fap2gzvyhtgzwglutf`

Ethereum (ETH):

`0x6Ab5F41A4eF61E6F7517f4D89f759c94500e66e1`

Every donation helps keep the project alive and motivates further development. Thank you!

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## License

GPL-3.0-or-later.
