from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from physioswarm.memory import MemoryGraph
from physioswarm.types import ExecutionArtifact, TaskSignal


class MemoryGraphTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "memory.sqlite3"
        self.memory = MemoryGraph(self.path)

    def tearDown(self) -> None:
        self.memory.close()
        self.temp_dir.cleanup()

    def test_memory_graph_stores_and_recalls_related_artifacts(self) -> None:
        task = TaskSignal("task-1", "draft evidence synthesis", urgency=0.6, noise=0.2, complexity=0.7)
        artifact = ExecutionArtifact(
            task_id="task-1",
            cell_id="cortex-1",
            route="deliberative",
            status="executed",
            notes=["evidence synthesis complete"],
        )

        self.memory.store_interaction(task, artifact)
        recalled = self.memory.recall("synthesis evidence", limit=1)

        self.assertEqual(len(recalled), 1)
        self.assertEqual(recalled[0]["task_id"], "task-1")
        self.assertIn("evidence synthesis", recalled[0]["summary"])

    def test_trust_curriculum_decays_and_recovers(self) -> None:
        self.memory.record_outcome("cortex-1", status="failed")
        self.memory.record_outcome("cortex-1", status="failed")
        lowered = self.memory.trust_score("cortex-1")

        self.memory.record_outcome("cortex-1", status="executed")
        recovered = self.memory.trust_score("cortex-1")

        self.assertLess(lowered, 0.5)
        self.assertGreater(recovered, lowered)
