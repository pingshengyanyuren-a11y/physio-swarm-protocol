from __future__ import annotations

import unittest

from physioswarm.cells import ReflexCell, ResearchCell
from physioswarm.runtime import PhysioSwarmRuntime
from physioswarm.workflow import WorkflowPlan, WorkflowStage


class WorkflowTest(unittest.TestCase):
    def test_workflow_plan_expands_stages_into_artifacts(self) -> None:
        runtime = PhysioSwarmRuntime(
            cells=[ReflexCell("reflex-1"), ResearchCell("cortex-1")],
            reserve_cells=[ResearchCell("reserve-cortex")],
        )
        plan = WorkflowPlan(
            name="research-assistant",
            stages=[
                WorkflowStage("triage", "halt urgent recursion", urgency=0.92, noise=0.1, complexity=0.2),
                WorkflowStage("analysis", "synthesize evidence", urgency=0.55, noise=0.3, complexity=0.8),
            ],
        )

        result = runtime.run_plan(plan)

        self.assertEqual(result["plan"], "research-assistant")
        self.assertEqual(len(result["artifacts"]), 2)
        self.assertEqual(result["artifacts"][0]["stage"], "triage")


if __name__ == "__main__":
    unittest.main()
