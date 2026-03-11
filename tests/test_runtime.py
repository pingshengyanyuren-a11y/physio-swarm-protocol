from __future__ import annotations

import unittest

from physioswarm.cells import ReflexCell, ResearchCell
from physioswarm.runtime import PhysioSwarmRuntime
from physioswarm.types import TaskSignal


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


if __name__ == "__main__":
    unittest.main()
