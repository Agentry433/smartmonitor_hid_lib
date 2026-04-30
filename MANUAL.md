# smartmonitor-hid Manual

## What This Library Is For

Use `smartmonitor-hid` when your program needs to work with 3.5" SmartMonitor
HID displays that:

- appear on Linux as `hidraw`
- accept precompiled `img.dat` themes
- expect runtime metric packets instead of full-frame bitmap updates

This is not a generic framebuffer renderer. It is a device-specific transport,
theme, and runtime library.

## Core Concepts

### 1. Theme Upload

The display expects a compiled theme file, usually named `img.dat`.

You upload it once:

```python
from pathlib import Path
from smartmonitor_hid import SmartMonitorClient

with SmartMonitorClient.auto() as client:
    client.upload_theme(Path("img.dat"))
```

### 2. Runtime Metrics

After the theme is uploaded, the host sends metric values by tag.

Example:

```python
from smartmonitor_hid import SmartMonitorClient

with SmartMonitorClient.auto() as client:
    client.send_runtime_metrics(
        {"CPU_TEMP": 1, "CPU_PERCENT": 3},
        {"CPU_TEMP": 45, "CPU_PERCENT": 17},
    )
```

### 3. Date and Time

The display also accepts a dedicated time packet:

```python
from smartmonitor_hid import SmartMonitorClient

with SmartMonitorClient.auto() as client:
    client.send_datetime()
```

## Main Public API

### `SmartMonitorHidTransport`

Low-level transport class.

Use it if you need direct HID-level control:

```python
from smartmonitor_hid import SmartMonitorHidTransport

with SmartMonitorHidTransport.auto() as transport:
    transport.send_datetime()
```

Main methods:
- `auto_detect_path()`
- `open()`
- `close()`
- `upload_theme(...)`
- `send_runtime_pairs(...)`
- `send_datetime(...)`

### `SmartMonitorClient`

Higher-level wrapper for most applications.

Main methods:
- `upload_theme(...)`
- `send_datetime(...)`
- `build_theme_tag_mapping(...)`
- `describe_theme_widgets(...)`
- `send_runtime_metrics(...)`

Recommended for normal application use.

### Theme Parsing and Compilation

Use:
- `parse_theme_bundle(...)`
- `parse_imgdat_file(...)`
- `ThemeCompiler()`
- `compile_theme_file(...)`

Example:

```python
from pathlib import Path
from smartmonitor_hid import ThemeCompiler

compiler = ThemeCompiler()
compiled = compiler.compile_ui_file("theme.ui")
Path("img.dat").write_bytes(compiled)
```

## Typical Usage Patterns

### Pattern 1: Upload an Existing Theme

```python
from pathlib import Path
from smartmonitor_hid import SmartMonitorClient

with SmartMonitorClient.auto() as client:
    client.upload_theme(Path("rog03-vendor.dat"))
    client.send_datetime()
```

### Pattern 2: Compile a `.ui` Theme and Upload It

```python
from pathlib import Path
from smartmonitor_hid import SmartMonitorClient, ThemeCompiler

compiler = ThemeCompiler()
compiled = compiler.compile_ui_file("theme.ui")
Path("generated.dat").write_bytes(compiled)

with SmartMonitorClient.auto() as client:
    client.upload_theme(Path("generated.dat"))
```

### Pattern 3: Build Runtime Mapping from Widgets

```python
from smartmonitor_hid import SmartMonitorClient, ThemeSensorSpec, ThemeWidgetSpec

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

client = SmartMonitorClient.auto()
mapping = client.build_theme_tag_mapping(widgets)
client.close()
```

## How To Integrate It Into Your Own Project

## Option A: Poll Your Own Sensors

If your program already collects sensor values, integration is simple:

1. Initialize the client
2. Upload the selected theme
3. Build or load a tag mapping
4. Periodically call `send_runtime_metrics(...)`
5. Periodically call `send_datetime(...)`

Example skeleton:

```python
import time
from pathlib import Path

from smartmonitor_hid import SmartMonitorClient


def collect_metrics():
    return {
        "CPU_TEMP": 43,
        "CPU_PERCENT": 12,
        "RAM_PERCENT": 51,
    }


def main():
    mapping = {
        "CPU_TEMP": 1,
        "CPU_PERCENT": 3,
        "RAM_PERCENT": 12,
    }

    with SmartMonitorClient.auto() as client:
        client.upload_theme(Path("img.dat"))
        client.send_datetime()

        while True:
            client.send_runtime_metrics(mapping, collect_metrics())
            time.sleep(1.0)
```

## Option B: Use It As a Backend Layer

If your application supports multiple display families:

- keep your existing display abstraction
- add a SmartMonitor HID backend
- call this library only when the selected display type is SmartMonitor HID

Recommended split:
- your app handles config, sensors, scheduling, and UI
- `smartmonitor-hid` handles SmartMonitor protocol, theme, and runtime packets

## Option C: Use It as a CLI Toolchain

For tooling workflows:

- compile themes from `.ui`
- inspect themes
- upload themes
- send time manually

Example:

```bash
smartmonitor-hid compile-ui theme.ui theme.dat
smartmonitor-hid upload-theme theme.dat
smartmonitor-hid send-time
```

## Tag Mapping Notes

The device does not receive named metrics like `"CPU_TEMP"` directly.
It receives numeric tags.

Your program must either:
- already know the correct mapping
- or build it from theme widgets using `build_theme_tag_mapping(...)`

If a widget in the theme does not declare a valid sensor/tag description,
runtime values will not appear there.

## `.ui` and `.img.dat`

### `.ui`

Vendor theme source format.

Use it when:
- inspecting a theme structure
- editing or generating themes
- compiling a new `img.dat`

### `.img.dat` / `.dat`

Compiled device format.

Use it when:
- uploading to the monitor
- reverse-inspecting compiled themes

## Bridge Layer

Most of the package already works standalone.

The optional bridge layer exists only for explicit host-project integration
cases. If needed:

```bash
export SMARTMONITOR_HID_PROJECT_ROOT=/path/to/project
```

or:

```python
from smartmonitor_hid import configure_project_root

configure_project_root("/path/to/project")
```

## Testing

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The included tests cover:
- runtime mapping
- client behavior
- CLI parser and bridge handling
- `.ui` roundtrip
- `.img.dat` parsing
- standalone compile flow

## Limitations

- Linux-oriented HID implementation
- no built-in GUI editor in this package
- no bundled sensor collectors
- some advanced vendor-specific compile behavior may still rely on donor-style fallbacks for best DateTime fidelity

## Recommended Integration Strategy

For most external projects, the best approach is:

1. keep your own sensor collection logic
2. use `smartmonitor-hid` only as the device/theme/runtime layer
3. isolate it behind your own display backend interface

That gives you a clean architecture and keeps SmartMonitor-specific logic out of
the rest of your application.
