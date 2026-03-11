from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from physioswarm.cells import ResearchCell
from physioswarm.distributed import DistributedTissueExecutor, NetworkTissueExecutor, TissueNodeServer
from physioswarm.types import TaskSignal


class _NodeHandler(BaseHTTPRequestHandler):
    region = "core"
    failing = False

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        status = 500 if self.failing else 200
        payload = b'{"status":"ok"}'
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers["Content-Length"])
        payload = self.rfile.read(length).decode("utf-8")
        if self.failing:
            body = b'{"error":"unavailable"}'
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True
            return
        response = (
            '{"task_id":"%s","cell_id":"%s-node","route":"network","status":"executed",'
            '"region":"%s","notes":["network tissue executed"],"resource_budget":1.0,"stress_level":0.2}'
        ) % (payload.split('"task_id": "')[1].split('"')[0], self.region, self.region)
        body = response.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.close_connection = True

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


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

    def test_network_tissue_executor_dispatches_to_multiple_nodes(self) -> None:
        cortex_handler = type("CortexHandler", (_NodeHandler,), {"region": "cortex"})
        hippo_handler = type("HippoHandler", (_NodeHandler,), {"region": "hippocampus"})
        cortex_server = ThreadingHTTPServer(("127.0.0.1", 0), cortex_handler)
        hippo_server = ThreadingHTTPServer(("127.0.0.1", 0), hippo_handler)
        cortex_thread = threading.Thread(target=cortex_server.serve_forever, daemon=True)
        hippo_thread = threading.Thread(target=hippo_server.serve_forever, daemon=True)
        cortex_thread.start()
        hippo_thread.start()
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = NetworkTissueExecutor(Path(temp_dir) / "network.sqlite3")
            try:
                tasks = [
                    TaskSignal("net-1", "draft evidence synthesis", urgency=0.5, noise=0.1, complexity=0.7, region="cortex"),
                    TaskSignal("net-2", "encode memory trace", urgency=0.4, noise=0.1, complexity=0.5, region="hippocampus"),
                ]
                artifacts = executor.run_batch(
                    tasks,
                    {
                        "cortex": f"http://127.0.0.1:{cortex_server.server_address[1]}",
                        "hippocampus": f"http://127.0.0.1:{hippo_server.server_address[1]}",
                    },
                )

                self.assertEqual(len(artifacts), 2)
                self.assertEqual({artifact["route"] for artifact in artifacts}, {"network"})
            finally:
                executor.close()
                cortex_server.shutdown()
                hippo_server.shutdown()
                cortex_server.server_close()
                hippo_server.server_close()
                cortex_thread.join(timeout=1)
                hippo_thread.join(timeout=1)

    def test_network_tissue_executor_fails_over_to_healthy_node(self) -> None:
        failing_handler = type("FailingHandler", (_NodeHandler,), {"region": "cortex", "failing": True})
        healthy_handler = type("HealthyHandler", (_NodeHandler,), {"region": "cortex", "failing": False})
        failing_server = ThreadingHTTPServer(("127.0.0.1", 0), failing_handler)
        healthy_server = ThreadingHTTPServer(("127.0.0.1", 0), healthy_handler)
        failing_thread = threading.Thread(target=failing_server.serve_forever, daemon=True)
        healthy_thread = threading.Thread(target=healthy_server.serve_forever, daemon=True)
        failing_thread.start()
        healthy_thread.start()
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = NetworkTissueExecutor(Path(temp_dir) / "network.sqlite3")
            try:
                artifacts = executor.run_batch(
                    [TaskSignal("net-failover", "draft evidence synthesis", urgency=0.5, noise=0.1, complexity=0.7, region="cortex")],
                    {
                        "cortex": [
                            f"http://127.0.0.1:{failing_server.server_address[1]}",
                            f"http://127.0.0.1:{healthy_server.server_address[1]}",
                        ]
                    },
                )

                self.assertEqual(len(artifacts), 1)
                self.assertEqual(artifacts[0]["route"], "network")
                self.assertEqual(artifacts[0]["cell_id"], "cortex-node")
            finally:
                executor.close()
                failing_server.shutdown()
                healthy_server.shutdown()
                failing_server.server_close()
                healthy_server.server_close()
                failing_thread.join(timeout=1)
                healthy_thread.join(timeout=1)

    def test_tissue_node_server_executes_real_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            node = TissueNodeServer(
                host="127.0.0.1",
                port=0,
                region="cortex",
                database_path=Path(temp_dir) / "node.sqlite3",
                cell_specs=[{"cell_id": "cortex-a", "region": "cortex", "organ": "cortex", "reliability": 0.9}],
            )
            try:
                node.start()
                endpoint = f"http://127.0.0.1:{node.port}/execute"
                body = json.dumps(
                    {
                        "task_id": "node-1",
                        "objective": "draft evidence synthesis",
                        "urgency": 0.5,
                        "noise": 0.1,
                        "complexity": 0.7,
                        "tags": [],
                        "region": "cortex",
                        "propagation_hops": 1,
                    }
                ).encode("utf-8")
                import urllib.request

                with urllib.request.urlopen(
                    urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST"),
                    timeout=10,
                ) as response:
                    artifact = json.loads(response.read().decode("utf-8"))

                self.assertEqual(artifact["status"], "executed")
                self.assertEqual(artifact["region"], "cortex")
            finally:
                node.stop()
