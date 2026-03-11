from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from physioswarm.cells import ReflexCell, ResearchCell
from physioswarm.latent_model import AdaptiveLatentModel
from physioswarm.memory import MemoryGraph
from physioswarm.runtime import PhysioSwarmRuntime
from physioswarm.topology import TissueTopology
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

    def test_runtime_prefers_local_tissue_cells_over_distant_cells(self) -> None:
        topology = TissueTopology()
        topology.connect("cortex", "hippocampus")
        topology.place("cortex-distant", "liver")
        topology.place("cortex-local", "cortex")
        runtime = PhysioSwarmRuntime(
            cells=[
                ResearchCell("cortex-distant", region="liver"),
                ResearchCell("cortex-local", region="cortex"),
            ],
            topology=topology,
        )

        artifact = runtime.handle(
            TaskSignal("local-1", "draft local synthesis", urgency=0.5, noise=0.1, complexity=0.6, region="cortex")
        )

        self.assertEqual(artifact.cell_id, "cortex-local")

    def test_runtime_builds_regional_homeostasis_from_hazard_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            memory = MemoryGraph(Path(temp_dir) / "memory.sqlite3")
            topology = TissueTopology()
            topology.place("cortex-1", "cortex")
            runtime = PhysioSwarmRuntime(
                cells=[ResearchCell("cortex-1", region="cortex", reliability=0.45)],
                memory_graph=memory,
                topology=topology,
            )
            try:
                noisy = TaskSignal(
                    "hazard-1",
                    "repair recursive failure",
                    urgency=0.5,
                    noise=0.95,
                    complexity=0.8,
                    region="cortex",
                )

                runtime.handle(noisy)
                runtime.handle(noisy)
                runtime.handle(
                    TaskSignal(
                        "followup-1",
                        "repair recursive failure again",
                        urgency=0.45,
                        noise=0.2,
                        complexity=0.5,
                        region="cortex",
                    )
                )
                regional = runtime.region_snapshot()

                self.assertGreater(regional["cortex"]["hazard_level"], 0.2)
                self.assertLess(regional["cortex"]["resource"], 1.0)
            finally:
                runtime.close()

    def test_runtime_uses_adaptive_latent_model_for_field_memory(self) -> None:
        topology = TissueTopology()
        topology.connect("cortex", "hippocampus")
        runtime = PhysioSwarmRuntime(
            cells=[ResearchCell("cortex-1", region="cortex"), ResearchCell("hippo-1", region="hippocampus")],
            topology=topology,
            latent_model=AdaptiveLatentModel(dimensions=32),
        )

        runtime.handle(
            TaskSignal("latent-1", "evidence synthesis memory", urgency=0.5, noise=0.1, complexity=0.6, region="cortex")
        )
        runtime.handle(
            TaskSignal("latent-2", "evidence drafting memory", urgency=0.5, noise=0.1, complexity=0.6, region="hippocampus")
        )
        matches = runtime.vector_bus.recall("evidence memory", limit=2)

        self.assertEqual(len(matches), 2)
        self.assertGreater(matches[0]["score"], 0.3)
        runtime.close()


if __name__ == "__main__":
    unittest.main()
