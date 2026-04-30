from __future__ import annotations

from dataclasses import dataclass, field
import unittest

from smartmonitor_hid.client import SmartMonitorClient


@dataclass
class FakeTransport:
    calls: list[tuple[int, list[tuple[int, int]]]] = field(default_factory=list)

    def send_runtime_pairs(self, command: int, pairs: list[tuple[int, int]]):
        self.calls.append((command, list(pairs)))


class SmartMonitorClientTests(unittest.TestCase):
    def test_send_runtime_metrics_rounds_clamps_and_filters(self):
        transport = FakeTransport()
        client = SmartMonitorClient(transport=transport)  # type: ignore[arg-type]

        pairs = client.send_runtime_metrics(
            tag_mapping={
                "CPU_TEMP": 1,
                "GPU_TEMP": 2,
                "RAM_PERCENT": 3,
                "MISSING": 4,
            },
            metric_values={
                "CPU_TEMP": 42.6,
                "GPU_TEMP": -3,
                "RAM_PERCENT": 999999,
            },
            command=0x22,
        )

        self.assertEqual(pairs, [(1, 43), (2, 0), (3, 65535)])
        self.assertEqual(transport.calls, [(0x22, [(1, 43), (2, 0), (3, 65535)])])

    def test_send_runtime_metrics_skips_transport_when_no_pairs(self):
        transport = FakeTransport()
        client = SmartMonitorClient(transport=transport)  # type: ignore[arg-type]

        pairs = client.send_runtime_metrics(tag_mapping={"CPU_TEMP": 1}, metric_values={})

        self.assertEqual(pairs, [])
        self.assertEqual(transport.calls, [])


if __name__ == "__main__":
    unittest.main()
