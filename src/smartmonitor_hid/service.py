from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import threading
import time
from typing import Callable, Mapping

from .client import SmartMonitorClient
from .errors import SmartMonitorTransportError


MetricCollector = Callable[[], Mapping[str, int | float]]
TimeProvider = Callable[[], datetime]


@dataclass(slots=True)
class RuntimeServiceStats:
    ticks: int = 0
    successful_ticks: int = 0
    failed_ticks: int = 0
    reconnects: int = 0
    last_pairs_sent: int = 0
    last_error: str = ""
    last_tick_monotonic: float = 0.0
    last_time_sync_monotonic: float = 0.0

    def to_dict(self) -> dict:
        return {
            "ticks": self.ticks,
            "successful_ticks": self.successful_ticks,
            "failed_ticks": self.failed_ticks,
            "reconnects": self.reconnects,
            "last_pairs_sent": self.last_pairs_sent,
            "last_error": self.last_error,
            "last_tick_monotonic": self.last_tick_monotonic,
            "last_time_sync_monotonic": self.last_time_sync_monotonic,
        }


@dataclass(slots=True)
class RuntimeServiceConfig:
    tick_interval: float = 1.0
    send_time_on_start: bool = True
    time_sync_interval: float = 60.0
    command: int = 0x02
    reconnect_attempts: int = 3
    recover_wait_after_close: float = 1.0
    continue_on_collector_error: bool = False


class SmartMonitorRuntimeService:
    def __init__(
        self,
        client: SmartMonitorClient,
        tag_mapping: Mapping[str, int],
        metric_collector: MetricCollector,
        *,
        config: RuntimeServiceConfig | None = None,
        time_provider: TimeProvider | None = None,
    ):
        self.client = client
        self.tag_mapping = {str(key): int(value) for key, value in tag_mapping.items()}
        self.metric_collector = metric_collector
        self.config = config or RuntimeServiceConfig()
        self.time_provider = time_provider or datetime.now
        self.stats = RuntimeServiceStats()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def send_time_if_due(self, *, force: bool = False):
        if self.config.time_sync_interval <= 0 and not force:
            return
        now = time.monotonic()
        if force or self.stats.last_time_sync_monotonic == 0.0 or (
            now - self.stats.last_time_sync_monotonic >= self.config.time_sync_interval
        ):
            self.client.send_datetime(self.time_provider())
            self.stats.last_time_sync_monotonic = now

    def run_once(self) -> list[tuple[int, int]]:
        self.stats.ticks += 1
        self.stats.last_tick_monotonic = time.monotonic()
        try:
            metrics = self.metric_collector()
        except Exception as exc:
            self.stats.failed_ticks += 1
            self.stats.last_error = str(exc)
            if self.config.continue_on_collector_error:
                return []
            raise

        try:
            pairs = self.client.send_runtime_metrics(
                self.tag_mapping,
                metrics,
                command=self.config.command,
            )
            self.stats.successful_ticks += 1
            self.stats.last_pairs_sent = len(pairs)
            self.stats.last_error = ""
            return pairs
        except SmartMonitorTransportError as exc:
            self.stats.failed_ticks += 1
            self.stats.last_error = str(exc)
            self.client.transport.recover(
                attempts=self.config.reconnect_attempts,
                wait_after_close=self.config.recover_wait_after_close,
            )
            self.stats.reconnects += 1
            raise

    def loop(self, stop_event: threading.Event | None = None):
        stop = stop_event or self._stop_event
        if self.config.send_time_on_start:
            self.send_time_if_due(force=True)
        while not stop.is_set():
            start = time.monotonic()
            try:
                self.run_once()
                self.send_time_if_due()
            except SmartMonitorTransportError:
                pass
            elapsed = time.monotonic() - start
            delay = max(0.0, self.config.tick_interval - elapsed)
            if stop.wait(delay):
                break

    def start_background(self) -> threading.Thread:
        if self._thread is not None and self._thread.is_alive():
            return self._thread
        self._stop_event.clear()
        self._thread = threading.Thread(target=self.loop, args=(self._stop_event,), daemon=True)
        self._thread.start()
        return self._thread

    def stop_background(self, timeout: float = 5.0):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        self._thread = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
