from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from physioswarm.cells import ResearchCell
from physioswarm.distributed import DistributedTissueExecutor
from physioswarm.types import TaskSignal


class DistributedExecutionTest(unittest.TestCase):
    def test_distributed_tissue_executor_processes_tasks_across_regions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = DistributedTissueExecutor(Path(temp_dir) / "distributed.sqlite3", max_workers=2)
            try:
                tasks = [
                    TaskSignal("cortex-1", "draft evidence synthesis", urgency=0.5, noise=0.1, complexity=0.7, region="cortex"),
                    TaskSignal("hippo-1", "encode memory trace", urgency=0.4, noise=0.1, complexity=0.5, region="hippocampus"),
                ]
                artifacts = executor.run_batch(
                    tasks,
                    cell_specs=[
                        {"cell_id": "cortex-a", "region": "cortex", "organ": "cortex", "reliability": 0.9},
                        {"cell_id": "hippo-a", "region": "hippocampus", "organ": "cortex", "reliability": 0.9},
                    ],
                )

                self.assertEqual(len(artifacts), 2)
                self.assertEqual({artifact["region"] for artifact in artifacts}, {"cortex", "hippocampus"})
            finally:
                executor.close()
