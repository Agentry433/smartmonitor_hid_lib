# Мануал по smartmonitor-hid

## Для чего нужна библиотека

Используйте `smartmonitor-hid`, если вашей программе нужно работать с
3.5" SmartMonitor HID-дисплеями, которые:

- видны в Linux как `hidraw`
- принимают заранее собранные темы `img.dat`
- ожидают runtime metric packets, а не полные bitmap-кадры

Это не универсальный framebuffer renderer. Это device-specific библиотека для
протокола, тем и runtime-пакетов SmartMonitor.

## Базовая модель работы

### 1. Загрузка темы

Монитор ожидает compiled theme file, обычно `img.dat`.

Её нужно загрузить:

```python
from pathlib import Path
from smartmonitor_hid import SmartMonitorClient

with SmartMonitorClient.auto() as client:
    client.upload_theme(Path("img.dat"))
```

### 2. Отправка runtime-метрик

После загрузки темы хост отправляет значения метрик по тегам.

Пример:

```python
from smartmonitor_hid import SmartMonitorClient

with SmartMonitorClient.auto() as client:
    client.send_runtime_metrics(
        {"CPU_TEMP": 1, "CPU_PERCENT": 3},
        {"CPU_TEMP": 45, "CPU_PERCENT": 17},
    )
```

### 3. Отправка даты и времени

Для времени используется отдельный пакет:

```python
from smartmonitor_hid import SmartMonitorClient

with SmartMonitorClient.auto() as client:
    client.send_datetime()
```

## Основной публичный API

### `SmartMonitorHidTransport`

Низкоуровневый transport class.

Используйте его, если нужен прямой HID-level control:

```python
from smartmonitor_hid import SmartMonitorHidTransport

with SmartMonitorHidTransport.auto() as transport:
    transport.send_datetime()
```

Основные методы:
- `auto_detect_path()`
- `open()`
- `close()`
- `upload_theme(...)`
- `send_runtime_pairs(...)`
- `send_datetime(...)`

### `SmartMonitorClient`

Более высокий уровень для обычных приложений.

Основные методы:
- `upload_theme(...)`
- `send_datetime(...)`
- `build_theme_tag_mapping(...)`
- `describe_theme_widgets(...)`
- `send_runtime_metrics(...)`

Для нормального использования чаще нужен именно он.

### Парсинг и компиляция тем

Используйте:
- `parse_theme_bundle(...)`
- `parse_imgdat_file(...)`
- `ThemeCompiler()`
- `compile_theme_file(...)`
- `describe_theme_bundle(...)`
- `validate_theme_bundle(...)`
- `compile_report(...)`
- `add_widget(...)`, `duplicate_widget(...)`, `remove_widget(...)`
- `set_widget_sensor(...)`, `set_widget_datetime_format(...)`

Пример:

```python
from pathlib import Path
from smartmonitor_hid import ThemeCompiler

compiler = ThemeCompiler()
compiled = compiler.compile_ui_file("theme.ui")
Path("img.dat").write_bytes(compiled)
```

### API валидации и отчётов

Используйте:
- `describe_theme_bundle(...)`
- `list_runtime_tags(...)`
- `list_supported_metrics(...)`
- `validate_theme_bundle(...)`
- `compile_report(...)`

Это рекомендуемый способ понять, что тема реально умеет, какие runtime-поля
она содержит и какие проблемы в ней есть ещё до загрузки в монитор.

### API программного редактирования тем

Используйте:
- `find_widget(...)`
- `add_widget(...)`
- `duplicate_widget(...)`
- `remove_widget(...)`
- `move_widget(...)`
- `set_widget_geometry(...)`
- `set_widget_sensor(...)`
- `clear_widget_sensor(...)`
- `set_widget_datetime_format(...)`

Этот слой нужен для программного редактирования тем без GUI-редактора.

### Managed Runtime Service

Используйте:
- `SmartMonitorRuntimeService`
- `RuntimeServiceConfig`
- `RuntimeServiceStats`

Этот слой нужен приложениям, которым требуется:
- периодически отправлять метрики
- периодически синхронизировать время
- автоматически восстанавливаться после transport errors
- запускать runtime loop в фоне, не переписывая эту логику заново

## Типовые сценарии

### Сценарий 1: Загрузить готовую тему

```python
from pathlib import Path
from smartmonitor_hid import SmartMonitorClient

with SmartMonitorClient.auto() as client:
    client.upload_theme(Path("rog03-vendor.dat"))
    client.send_datetime()
```

### Сценарий 2: Скомпилировать `.ui` и загрузить

```python
from pathlib import Path
from smartmonitor_hid import SmartMonitorClient, ThemeCompiler

compiler = ThemeCompiler()
compiled = compiler.compile_ui_file("theme.ui")
Path("generated.dat").write_bytes(compiled)

with SmartMonitorClient.auto() as client:
    client.upload_theme(Path("generated.dat"))
```

### Сценарий 3: Построить mapping из widgets

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

## Как подключать библиотеку в свои проекты

## Вариант A: У вас уже есть свои датчики

Если ваша программа уже умеет собирать значения датчиков, интеграция простая:

1. создать client
2. загрузить выбранную тему
3. построить или взять готовый tag mapping
4. периодически вызывать `send_runtime_metrics(...)`
5. периодически вызывать `send_datetime(...)`

Пример каркаса:

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

## Вариант B: Использовать как backend слой

Если ваше приложение поддерживает несколько семейств дисплеев:

- оставьте свою общую display abstraction
- добавьте отдельный SmartMonitor HID backend
- вызывайте эту библиотеку только когда выбран SmartMonitor HID

Рекомендуемое разделение:
- ваше приложение отвечает за config, sensors, scheduling и UI
- `smartmonitor-hid` отвечает за SmartMonitor protocol, themes и runtime packets

## Вариант C: Использовать как CLI toolchain

Для tooling workflows:

- компилировать темы из `.ui`
- разбирать темы
- загружать темы
- вручную отправлять время

Пример:

```bash
smartmonitor-hid compile-ui theme.ui theme.dat
smartmonitor-hid upload-theme theme.dat
smartmonitor-hid send-time
```

## Вариант D: Использовать готовый runtime service

Если не хочется писать собственный runtime loop, можно использовать встроенный
service-слой:

```python
from smartmonitor_hid import RuntimeServiceConfig, SmartMonitorClient, SmartMonitorRuntimeService


def collect_metrics():
    return {
        "CPU_TEMP": 43,
        "CPU_PERCENT": 12,
    }


with SmartMonitorClient.auto() as client:
    service = SmartMonitorRuntimeService(
        client=client,
        tag_mapping={"CPU_TEMP": 1, "CPU_PERCENT": 3},
        metric_collector=collect_metrics,
        config=RuntimeServiceConfig(
            tick_interval=1.0,
            send_time_on_start=True,
            time_sync_interval=60.0,
        ),
    )
    service.start_background()
```

## Что важно знать про tag mapping

Монитор не получает named metrics вроде `"CPU_TEMP"` напрямую.
Он получает числовые теги.

Значит ваше приложение должно либо:
- уже знать правильный mapping
- либо строить его из widgets темы через `build_theme_tag_mapping(...)`

Если widget в теме не содержит корректного sensor/tag описания,
runtime-значения в него не попадут.

## Что такое `.ui` и `.img.dat`

### `.ui`

Исходный vendor theme format.

Используйте его, когда нужно:
- разбирать структуру темы
- редактировать или генерировать темы
- компилировать новый `img.dat`

### `.img.dat` / `.dat`

Скомпилированный формат для устройства.

Используйте его, когда нужно:
- заливать тему в монитор
- анализировать уже собранные темы

## Bridge-слой

Большая часть библиотеки уже работает standalone.

Опциональный bridge нужен только для специальных сценариев host-project
integration. Если он нужен:

```bash
export SMARTMONITOR_HID_PROJECT_ROOT=/path/to/project
```

или:

```python
from smartmonitor_hid import configure_project_root

configure_project_root("/path/to/project")
```

## Тестирование

Запуск:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Тесты покрывают:
- runtime mapping
- client behavior
- CLI parser и bridge handling
- validation/reporting API
- theme manipulation API
- managed runtime service
- `.ui` roundtrip
- `.img.dat` parsing
- standalone compile flow

## Ограничения

- Linux-ориентированная HID-реализация
- в самой библиотеке нет GUI-редактора
- нет встроенных sensor collectors
- часть продвинутого vendor-specific compile behavior может всё ещё использовать donor-style fallback для лучшей точности DateTime

## Рекомендуемая стратегия интеграции

Для большинства внешних проектов лучший путь такой:

1. оставить свою sensor collection logic
2. использовать `smartmonitor-hid` только как device/theme/runtime layer
3. изолировать её за своим display backend interface

Так архитектура остаётся чистой, а вся SmartMonitor-specific логика не
размазывается по остальному приложению.
