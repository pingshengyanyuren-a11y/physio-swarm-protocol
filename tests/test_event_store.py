from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from physioswarm.cells import ReflexCell, ResearchCell
from physioswarm.runtime import PhysioSwarmRuntime
from physioswarm.types import TaskSignal


class EventStoreTest(unittest.TestCase):
    def test_runtime_persists_and_replays_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            store_path = Path(tmp_dir) / "events.jsonl"
            runtime = PhysioSwarmRuntime(
                cells=[ReflexCell("reflex-1"), ResearchCell("cortex-1")],
                event_log_path=store_path,
            )

            runtime.handle(TaskSignal("urgent-1", "halt runaway loop", urgency=0.95, noise=0.1, complexity=0.2))
            runtime.handle(TaskSignal("deep-1", "synthesize evidence", urgency=0.55, noise=0.3, complexity=0.82))

            self.assertTrue(store_path.exists())
            replayed = runtime.replay_events()

            self.assertGreaterEqual(len(replayed), 4)
            event_types = {event["event_type"] for event in replayed}
            self.assertIn("signal", event_types)
            self.assertIn("artifact", event_types)


if __name__ == "__main__":
    unittest.main()
