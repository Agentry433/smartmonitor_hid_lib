# smartmonitor-hid

[![Tests](https://img.shields.io/badge/tests-31%20passing-brightgreen)](./tests)
[![License](https://img.shields.io/badge/license-GPL--3.0--or--later-blue.svg)](./LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](./CHANGELOG.md)

Отдельная Python-библиотека для 3.5" SmartMonitor HID-дисплеев под Linux.

`smartmonitor-hid` нужна для проектов, которым требуется:

- обнаружить SmartMonitor HID-монитор
- загрузить в него готовую тему `img.dat` / `.dat`
- отправлять runtime-значения датчиков и текущее время
- разбирать vendor `.ui` темы
- компилировать `.ui` темы в готовый `img.dat`

Эта библиотека держит SmartMonitor HID protocol и workflow тем отдельно от
обычных bitmap-driven приложений для дисплеев.

Активный репозиторий:
- https://github.com/Agentry433/smartmonitor_hid_lib

## Возможности

- автоопределение HID-устройства через `hidraw`
- reset / YMODEM theme upload
- отправка runtime metric packets
- отправка пакетов даты и времени
- managed runtime loop / reconnect helpers
- helper-функции для runtime tag mapping
- API для валидации и отчётов по темам
- API для программного редактирования тем
- самостоятельный `.ui` parser / writer
- самостоятельный `.img.dat` parser / record packer
- самостоятельный `.ui -> img.dat` compiler
- CLI entry point: `smartmonitor-hid`
- тесты для non-hardware части библиотеки

## Требования

- Python `3.11+`
- Linux с доступом к `/dev/hidraw*`
- `Pillow`
- для текстового compiler path желательно иметь `fc-match`

## Установка

### Из локального checkout

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install .
```

### Editable install для разработки

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Быстрый старт

### Найти монитор

```bash
smartmonitor-hid detect
```

### Загрузить тему

```bash
smartmonitor-hid upload-theme path/to/img.dat
```

### Отправить текущую дату и время

```bash
smartmonitor-hid send-time
```

### Разобрать vendor `.ui`

```bash
smartmonitor-hid inspect-ui theme.ui
```

### Скомпилировать `.ui` тему

```bash
smartmonitor-hid compile-ui theme.ui output.dat
```

## Python-пример

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

## Валидация и отчёты

```python
from smartmonitor_hid import compile_report, describe_theme_bundle, parse_theme_bundle, validate_theme_bundle

bundle = parse_theme_bundle("theme.ui")
description = describe_theme_bundle(bundle)
validation = validate_theme_bundle(bundle)
report = compile_report(bundle)
```

## Редактирование тем

```python
from smartmonitor_hid import duplicate_widget, parse_theme_bundle, set_widget_datetime_format, set_widget_sensor

bundle = parse_theme_bundle("theme.ui")
duplicate_widget(bundle, object_name="clock", new_object_name="clock_copy", dx=10, dy=0)
set_widget_datetime_format(bundle, object_name="clock_copy", datetime_format="yyyy-MM-dd")
set_widget_sensor(
    bundle,
    object_name="cpu_temp",
    fast_sensor=1,
    sensor_type_name="Temperature",
    sensor_name="CPU Package",
    reading_name="CPU Temperature",
)
```

## Managed Runtime Service

```python
from smartmonitor_hid import RuntimeServiceConfig, SmartMonitorClient, SmartMonitorRuntimeService

with SmartMonitorClient.auto() as client:
    service = SmartMonitorRuntimeService(
        client=client,
        tag_mapping={"CPU_TEMP": 1, "CPU_PERCENT": 3},
        metric_collector=lambda: {"CPU_TEMP": 44, "CPU_PERCENT": 18},
        config=RuntimeServiceConfig(tick_interval=1.0, time_sync_interval=60.0),
    )
    service.start_background()
```

## Командная строка

```bash
smartmonitor-hid detect
smartmonitor-hid upload-theme img.dat
smartmonitor-hid send-time
smartmonitor-hid inspect-ui theme.ui
smartmonitor-hid inspect-imgdat img.dat
smartmonitor-hid compile-ui theme.ui output.dat
smartmonitor-hid map-ui theme.ui
```

Также можно запускать как модуль:

```bash
python -m smartmonitor_hid detect
```

## Bridge-конфигурация

Для transport, runtime, `.ui`, `.img.dat` и compile flows библиотека уже
работает самостоятельно.

Опциональный bridge-слой остаётся только для случаев, когда вы хотите
подтягивать дополнительные host-project модули из другого репозитория. Для
этого можно использовать:

```bash
export SMARTMONITOR_HID_PROJECT_ROOT=/path/to/project
```

или:

```python
from smartmonitor_hid import configure_project_root

configure_project_root("/path/to/project")
```

## Документация

- [MANUAL.md](MANUAL.md) - полный мануал по использованию и интеграции
- [README.md](README.md) - английский обзор
- [MANUAL_RU.md](MANUAL_RU.md) - русский мануал по использованию и интеграции

## Поддержка проекта

Если библиотека оказалась полезной, можно поддержать её разработку донатом:

TON Wallet:

`UQAnWldcIWfwKUmnJN5kMqW5VY6SuVwTtrnRpDEE_rilh8Qj`

Bitcoin (BTC):

`bc1qelwv8jm2j9pughk5rte0fap2gzvyhtgzwglutf`

Ethereum (ETH):

`0x6Ab5F41A4eF61E6F7517f4D89f759c94500e66e1`

Каждый донат помогает поддерживать проект и мотивирует развивать его дальше. Спасибо!

## Тесты

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Лицензия

GPL-3.0-or-later.
