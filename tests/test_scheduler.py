from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from physioswarm.cells import ResearchCell
from physioswarm.runtime import PhysioSwarmRuntime
from physioswarm.scheduler import PersistentScheduler
from physioswarm.types import TaskSignal


class SchedulerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "scheduler.sqlite3"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_scheduler_persists_due_tasks_across_instances(self) -> None:
        scheduler = PersistentScheduler(self.path)
        due_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        scheduler.schedule(
            TaskSignal("task-1", "draft synthesis", urgency=0.5, noise=0.1, complexity=0.7),
            due_at=due_at,
        )
        scheduler.close()

        reloaded = PersistentScheduler(self.path)
        tasks = reloaded.claim_due(now=datetime.now(timezone.utc))

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task_id, "task-1")
        reloaded.close()

    def test_scheduler_runs_pending_tasks_and_marks_completion(self) -> None:
        scheduler = PersistentScheduler(self.path)
        due_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        scheduler.schedule(
            TaskSignal("task-2", "draft synthesis", urgency=0.5, noise=0.1, complexity=0.7),
            due_at=due_at,
        )
        runtime = PhysioSwarmRuntime(cells=[ResearchCell("cortex-1")])

        artifacts = scheduler.run_pending(runtime, now=datetime.now(timezone.utc))
        status_rows = scheduler.list_tasks()

        self.assertEqual(len(artifacts), 1)
        self.assertEqual(status_rows[0]["status"], "completed")
        scheduler.close()
