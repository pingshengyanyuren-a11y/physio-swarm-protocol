from __future__ import annotations

import json
import sqlite3
import threading
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError

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


class ClusterRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cluster_nodes (
                region TEXT NOT NULL,
                endpoint TEXT PRIMARY KEY,
                healthy INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        self.connection.commit()

    def register(self, region: str, endpoint: str) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO cluster_nodes (region, endpoint, healthy) VALUES (?, ?, COALESCE((SELECT healthy FROM cluster_nodes WHERE endpoint = ?), 1))",
            (region, endpoint, endpoint),
        )
        self.connection.commit()

    def mark_health(self, endpoint: str, healthy: bool) -> None:
        self.connection.execute(
            "UPDATE cluster_nodes SET healthy = ? WHERE endpoint = ?",
            (1 if healthy else 0, endpoint),
        )
        self.connection.commit()

    def resolve(self, region: str) -> str:
        row = self.connection.execute(
            """
            SELECT endpoint FROM cluster_nodes
            WHERE region = ? AND healthy = 1
            ORDER BY endpoint ASC
            LIMIT 1
            """,
            (region,),
        ).fetchone()
        if row is None:
            raise LookupError(f"no healthy endpoint for region {region}")
        return str(row["endpoint"])

    def endpoints(self, region: str) -> list[str]:
        rows = self.connection.execute(
            "SELECT endpoint FROM cluster_nodes WHERE region = ? ORDER BY endpoint ASC",
            (region,),
        ).fetchall()
        return [str(row["endpoint"]) for row in rows]

    def close(self) -> None:
        self.connection.close()


class NetworkTissueExecutor:
    def __init__(self, path: Path, timeout_seconds: float = 10.0) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.timeout_seconds = timeout_seconds
        self.registry = ClusterRegistry(path.with_name(f"{path.stem}-cluster.sqlite3"))
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS network_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                region TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                artifact TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def run_batch(self, tasks: list[TaskSignal], endpoints: dict[str, str | list[str]]) -> list[dict[str, object]]:
        for region, value in endpoints.items():
            candidates = value if isinstance(value, list) else [value]
            for endpoint in candidates:
                self.registry.register(region, endpoint)
        artifacts: list[dict[str, object]] = []
        for task in tasks:
            artifact = self._execute_with_failover(task)
            artifacts.append(artifact)
            self.connection.execute(
                "INSERT INTO network_runs (task_id, region, endpoint, artifact) VALUES (?, ?, ?, ?)",
                (task.task_id, task.region, artifact["_endpoint"], json.dumps(artifact)),
            )
        self.connection.commit()
        return artifacts

    def close(self) -> None:
        self.connection.close()
        self.registry.close()

    def _execute_with_failover(self, task: TaskSignal) -> dict[str, object]:
        endpoints = self.registry.endpoints(task.region)
        last_error: Exception | None = None
        for base in endpoints:
            try:
                if not self._check_health(base):
                    self.registry.mark_health(base, healthy=False)
                    continue
                artifact = self._post_task(base, task)
                self.registry.mark_health(base, healthy=True)
                artifact["_endpoint"] = base
                return artifact
            except (HTTPError, URLError, TimeoutError, OSError, LookupError, ValueError) as error:
                self.registry.mark_health(base, healthy=False)
                last_error = error
                continue
        raise RuntimeError(f"no reachable tissue endpoint for region {task.region}") from last_error

    def _check_health(self, base: str) -> bool:
        endpoint = base.rstrip("/") + "/health"
        with request.urlopen(endpoint, timeout=self.timeout_seconds) as response:
            return int(getattr(response, "status", 200)) < 400

    def _post_task(self, base: str, task: TaskSignal) -> dict[str, object]:
        endpoint = base.rstrip("/") + "/execute"
        body = json.dumps(asdict(task)).encode("utf-8")
        http_request = request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


class _TissueNodeHandler(BaseHTTPRequestHandler):
    runtime: PhysioSwarmRuntime | None = None
    region: str = "core"

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        payload = b'{"status":"ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/execute":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        task = TaskSignal(**payload)
        artifact = asdict(self.runtime.handle(task))
        encoded = json.dumps(artifact).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(encoded)
        self.close_connection = True

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


class TissueNodeServer:
    def __init__(
        self,
        host: str,
        port: int,
        region: str,
        database_path: Path,
        cell_specs: list[dict[str, object]],
    ) -> None:
        self.host = host
        self.port = port
        self.region = region
        self.database_path = database_path
        self.cell_specs = cell_specs
        self._thread: threading.Thread | None = None
        self._server: ThreadingHTTPServer | None = None
        self._runtime: PhysioSwarmRuntime | None = None

    def start(self) -> None:
        topology = TissueTopology()
        cells = _build_cells(self.cell_specs)
        self._runtime = PhysioSwarmRuntime(cells=cells, topology=topology)
        handler = type(
            f"{self.region.title()}TissueNodeHandler",
            (_TissueNodeHandler,),
            {"runtime": self._runtime, "region": self.region},
        )
        self._server = ThreadingHTTPServer((self.host, self.port), handler)
        self.port = int(self._server.server_address[1])
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=1)
        if self._runtime is not None:
            self._runtime.close()
