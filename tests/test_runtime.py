from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from physioswarm.cells import ReflexCell, ResearchCell
from physioswarm.memory import MemoryGraph
from physioswarm.runtime import PhysioSwarmRuntime
from physioswarm.types import TaskSignal
from physioswarm.vector_bus import SemanticVectorBus


class RuntimeTest(unittest.TestCase):
    def test_runtime_routes_urgent_low_noise_task_to_reflex_cell(self) -> None:
        runtime = PhysioSwarmRuntime(
            cells=[
                ReflexCell("reflex-1"),
                ResearchCell("cortex-1"),
            ]
        )

        artifact = runtime.handle(
            TaskSignal("urgent-1", "halt recursion", urgency=0.95, noise=0.1, complexity=0.2)
        )

        self.assertEqual(artifact.route, "fast_lane")
        self.assertEqual(artifact.cell_id, "reflex-1")

    def test_runtime_quarantines_unreliable_cell_after_failures(self) -> None:
        runtime = PhysioSwarmRuntime(cells=[ResearchCell("cortex-risky", reliability=0.45)])
        task = TaskSignal("noisy-1", "review noisy findings", urgency=0.4, noise=0.95, complexity=0.8)

        runtime.handle(task)
        runtime.handle(task)

        self.assertTrue(runtime.cell_state("cortex-risky").quarantined)

    def test_runtime_contracts_budget_under_pressure(self) -> None:
        runtime = PhysioSwarmRuntime(cells=[ReflexCell("reflex-1"), ResearchCell("cortex-1")])
        runtime.handle(TaskSignal("t1", "urgent stabilize", urgency=0.95, noise=0.1, complexity=0.2))
        runtime.handle(TaskSignal("t2", "long synthesis", urgency=0.6, noise=0.4, complexity=0.9))

        self.assertLess(runtime.state.resource_budget, 1.0)

    def test_runtime_records_signal_events(self) -> None:
        runtime = PhysioSwarmRuntime(cells=[ResearchCell("cortex-risky", reliability=0.45)])
        task = TaskSignal("noisy-1", "review noisy findings", urgency=0.4, noise=0.95, complexity=0.8)

        runtime.handle(task)
        runtime.handle(task)

        channels = [event["signal"]["channel"] for event in runtime.signal_history]
        self.assertIn("endocrine", channels)
        self.assertIn("immune", channels)

    def test_runtime_updates_memory_and_vector_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory = MemoryGraph(Path(temp_dir) / "memory.sqlite3")
            vector_bus = SemanticVectorBus()
            runtime = PhysioSwarmRuntime(
                cells=[ResearchCell("cortex-1")],
                memory_graph=memory,
                vector_bus=vector_bus,
            )

            runtime.handle(TaskSignal("t-memory", "draft evidence synthesis", urgency=0.5, noise=0.1, complexity=0.7))

            recalled = memory.recall("evidence", limit=1)
            matches = vector_bus.recall("evidence drafting", limit=1)

            self.assertEqual(recalled[0]["task_id"], "t-memory")
            self.assertEqual(matches[0]["task_id"], "t-memory")
            runtime.close()


if __name__ == "__main__":
    unittest.main()
