from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import threading
import time
import unittest

from smartmonitor_hid.errors import SmartMonitorTransportError
from smartmonitor_hid.service import RuntimeServiceConfig, SmartMonitorRuntimeService


@dataclass
class FakeTransport:
    recovered: int = 0

    def recover(self, attempts: int = 3, wait_after_close: float = 1.0, flush_input: bool = True):
        self.recovered += 1


@dataclass
class FakeClient:
    transport: FakeTransport = field(default_factory=FakeTransport)
    sent_pairs: list[list[tuple[int, int]]] = field(default_factory=list)
    sent_times: list[datetime] = field(default_factory=list)
    fail_once: bool = False

    def send_runtime_metrics(self, tag_mapping, metric_values, command=0x02):
        if self.fail_once:
            self.fail_once = False
            raise SmartMonitorTransportError("temporary transport failure")
        pairs = []
        for key, tag in tag_mapping.items():
            if key in metric_values:
                pairs.append((int(tag), int(metric_values[key])))
        self.sent_pairs.append(pairs)
        return pairs

    def send_datetime(self, when=None):
        self.sent_times.append(when or datetime.now())


class RuntimeServiceTests(unittest.TestCase):
    def test_run_once_sends_pairs(self):
        client = FakeClient()
        service = SmartMonitorRuntimeService(
            client=client,  # type: ignore[arg-type]
            tag_mapping={"CPU_TEMP": 1},
            metric_collector=lambda: {"CPU_TEMP": 42},
        )

        pairs = service.run_once()

        self.assertEqual(pairs, [(1, 42)])
        self.assertEqual(service.stats.successful_ticks, 1)
        self.assertEqual(service.stats.last_pairs_sent, 1)

    def test_run_once_recovers_on_transport_error(self):
        client = FakeClient(fail_once=True)
        service = SmartMonitorRuntimeService(
            client=client,  # type: ignore[arg-type]
            tag_mapping={"CPU_TEMP": 1},
            metric_collector=lambda: {"CPU_TEMP": 42},
        )

        with self.assertRaises(SmartMonitorTransportError):
            service.run_once()

        self.assertEqual(client.transport.recovered, 1)
        self.assertEqual(service.stats.failed_ticks, 1)
        self.assertEqual(service.stats.reconnects, 1)

    def test_loop_sends_time_on_start(self):
        client = FakeClient()
        stop = threading.Event()
        service = SmartMonitorRuntimeService(
            client=client,  # type: ignore[arg-type]
            tag_mapping={"CPU_TEMP": 1},
            metric_collector=lambda: {"CPU_TEMP": 42},
            config=RuntimeServiceConfig(tick_interval=0.01, time_sync_interval=999.0),
            time_provider=lambda: datetime(2026, 1, 1, 12, 0, 0),
        )

        thread = threading.Thread(target=service.loop, args=(stop,), daemon=True)
        thread.start()
        time.sleep(0.05)
        stop.set()
        thread.join(timeout=1.0)

        self.assertGreaterEqual(len(client.sent_times), 1)
        self.assertGreaterEqual(service.stats.successful_ticks, 1)

    def test_background_start_and_stop(self):
        client = FakeClient()
        service = SmartMonitorRuntimeService(
            client=client,  # type: ignore[arg-type]
            tag_mapping={"CPU_TEMP": 1},
            metric_collector=lambda: {"CPU_TEMP": 42},
            config=RuntimeServiceConfig(tick_interval=0.01),
        )

        service.start_background()
        time.sleep(0.05)
        self.assertTrue(service.is_running)
        service.stop_background()
        self.assertFalse(service.is_running)


if __name__ == "__main__":
    unittest.main()
