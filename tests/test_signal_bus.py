from __future__ import annotations

import unittest

from physioswarm.signal_bus import SignalBus
from physioswarm.types import ControlSignal


class SignalBusTest(unittest.TestCase):
    def test_broadcast_signal_reaches_all_subscribers(self) -> None:
        bus = SignalBus()
        bus.subscribe("endocrine", "cell:a")
        bus.subscribe("endocrine", "cell:b")

        delivered = bus.emit(ControlSignal(channel="endocrine", payload={"stress": 0.7}))

        self.assertEqual(set(delivered), {"cell:a", "cell:b"})

    def test_targeted_signal_hits_only_target(self) -> None:
        bus = SignalBus()
        bus.subscribe("immune", "cell:a")
        bus.subscribe("immune", "cell:b")

        delivered = bus.emit(ControlSignal(channel="immune", payload={"quarantine": True}, target="cell:b"))

        self.assertEqual(delivered, ["cell:b"])


if __name__ == "__main__":
    unittest.main()
