from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .types import ExecutionArtifact, TaskSignal


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PersistentScheduler:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                task_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                due_at TEXT NOT NULL,
                status TEXT NOT NULL,
                claimed_at TEXT,
                completed_at TEXT,
                artifact TEXT
            );
            """
        )
        self.connection.commit()

    def schedule(self, task: TaskSignal, due_at: datetime) -> None:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO scheduled_tasks
            (task_id, payload, due_at, status, claimed_at, completed_at, artifact)
            VALUES (?, ?, ?, ?, NULL, NULL, NULL)
            """,
            (task.task_id, json.dumps(asdict(task)), due_at.astimezone(timezone.utc).isoformat(), "scheduled"),
        )
        self.connection.commit()

    def claim_due(self, now: datetime | None = None) -> list[TaskSignal]:
        now = (now or _utc_now()).astimezone(timezone.utc).isoformat()
        rows = self.connection.execute(
            """
            SELECT task_id, payload FROM scheduled_tasks
            WHERE status = 'scheduled' AND due_at <= ?
            ORDER BY due_at ASC
            """,
            (now,),
        ).fetchall()
        tasks = [TaskSignal(**json.loads(row["payload"])) for row in rows]
        if rows:
            self.connection.executemany(
                "UPDATE scheduled_tasks SET status = 'claimed', claimed_at = ? WHERE task_id = ?",
                [(_utc_now().isoformat(), row["task_id"]) for row in rows],
            )
            self.connection.commit()
        return tasks

    def mark_completed(self, artifact: ExecutionArtifact) -> None:
        self.connection.execute(
            """
            UPDATE scheduled_tasks
            SET status = 'completed', completed_at = ?, artifact = ?
            WHERE task_id = ?
            """,
            (_utc_now().isoformat(), json.dumps(asdict(artifact)), artifact.task_id),
        )
        self.connection.commit()

    def run_pending(self, runtime, now: datetime | None = None) -> list[ExecutionArtifact]:
        tasks = self.claim_due(now=now)
        artifacts: list[ExecutionArtifact] = []
        for task in tasks:
            artifact = runtime.handle(task)
            self.mark_completed(artifact)
            artifacts.append(artifact)
        return artifacts

    def list_tasks(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """
            SELECT task_id, due_at, status, claimed_at, completed_at, artifact
            FROM scheduled_tasks
            ORDER BY due_at ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self.connection.close()
