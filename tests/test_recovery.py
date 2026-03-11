from __future__ import annotations

import unittest

from physioswarm.cells import ReflexCell, ResearchCell
from physioswarm.runtime import PhysioSwarmRuntime
from physioswarm.types import TaskSignal


class RecoveryTest(unittest.TestCase):
    def test_runtime_promotes_reserve_cell_when_primary_is_quarantined(self) -> None:
        runtime = PhysioSwarmRuntime(
            cells=[ResearchCell("cortex-risky", reliability=0.45)],
            reserve_cells=[ResearchCell("reserve-cortex", reliability=0.9)],
        )
        noisy = TaskSignal("noisy-1", "review noisy findings", urgency=0.4, noise=0.95, complexity=0.8)

        runtime.handle(noisy)
        runtime.handle(noisy)

        self.assertTrue(runtime.cell_state("cortex-risky").quarantined)
        self.assertIn("reserve-cortex", runtime.active_cells())

    def test_runtime_recovery_pool_can_restore_a_cell(self) -> None:
        runtime = PhysioSwarmRuntime(
            cells=[ResearchCell("cortex-risky", reliability=0.45), ReflexCell("reflex-1")],
            reserve_cells=[ResearchCell("reserve-cortex", reliability=0.9)],
        )
        noisy = TaskSignal("noisy-1", "review noisy findings", urgency=0.4, noise=0.95, complexity=0.8)

        runtime.handle(noisy)
        runtime.handle(noisy)
        runtime.recover_quarantined_cells()

        self.assertFalse(runtime.cell_state("cortex-risky").quarantined)


if __name__ == "__main__":
    unittest.main()
