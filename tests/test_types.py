from __future__ import annotations

import unittest

from physioswarm.types import CellState, HomeostasisState, TaskSignal


class TypesTest(unittest.TestCase):
    def test_homeostasis_balanced_defaults(self) -> None:
        state = HomeostasisState()

        self.assertAlmostEqual(state.stress_level, 0.2)
        self.assertAlmostEqual(state.resource_budget, 1.0)
        self.assertAlmostEqual(state.exploration_level, 0.45)

    def test_task_signal_marks_reflex_candidates(self) -> None:
        urgent = TaskSignal("t1", "stabilize", urgency=0.92, noise=0.1, complexity=0.2)
        deep = TaskSignal("t2", "synthesize", urgency=0.5, noise=0.35, complexity=0.85)

        self.assertTrue(urgent.qualifies_for_fast_lane())
        self.assertFalse(deep.qualifies_for_fast_lane())

    def test_cell_state_reports_fatigue(self) -> None:
        cell = CellState(cell_id="c1", organ="cortex", energy=0.18, load=0.9)
        self.assertTrue(cell.is_fatigued)


if __name__ == "__main__":
    unittest.main()
