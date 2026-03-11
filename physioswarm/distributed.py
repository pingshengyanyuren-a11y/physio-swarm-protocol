from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

from .cells import ResearchCell
from .runtime import PhysioSwarmRuntime
from .topology import TissueTopology
from .types import TaskSignal


def _build_cells(cell_specs: list[dict[str, object]]) -> list[ResearchCell]:
    cells: list[ResearchCell] = []
    for spec in cell_specs:
        cells.append(
            ResearchCell(
                str(spec["cell_id"]),
                reliability=float(spec.get("reliability", 0.9)),
                region=str(spec.get("region", "core")),
            )
        )
    return cells


def _run_region_task(payload: dict[str, object]) -> dict[str, object]:
    task = TaskSignal(**payload["task"])
    topology = TissueTopology()
    topology.place(str(payload["cell_specs"][0]["cell_id"]), task.region)
    runtime = PhysioSwarmRuntime(
        cells=_build_cells(payload["cell_specs"]),
        topology=topology,
    )
    try:
        artifact = runtime.handle(task)
        return asdict(artifact)
    finally:
        runtime.close()


class DistributedTissueExecutor:
    def __init__(self, path: Path, max_workers: int = 2) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.max_workers = max_workers
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS distributed_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                region TEXT NOT NULL,
                artifact TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def run_batch(self, tasks: list[TaskSignal], cell_specs: list[dict[str, object]]) -> list[dict[str, object]]:
        region_specs: dict[str, list[dict[str, object]]] = {}
        for spec in cell_specs:
            region_specs.setdefault(str(spec.get("region", "core")), []).append(spec)
        payloads = [
            {
                "task": asdict(task),
                "cell_specs": region_specs.get(task.region, cell_specs),
            }
            for task in tasks
        ]
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            artifacts = list(executor.map(_run_region_task, payloads))
        self.connection.executemany(
            "INSERT INTO distributed_runs (task_id, region, artifact) VALUES (?, ?, ?)",
            [(artifact["task_id"], artifact["region"], json.dumps(artifact)) for artifact in artifacts],
        )
        self.connection.commit()
        return artifacts

    def close(self) -> None:
        self.connection.close()
