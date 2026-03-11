from __future__ import annotations

import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from physioswarm.cells import ResearchCell
from physioswarm.distributed import DistributedTissueExecutor, NetworkTissueExecutor
from physioswarm.types import TaskSignal


class _NodeHandler(BaseHTTPRequestHandler):
    region = "core"

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers["Content-Length"])
        payload = self.rfile.read(length).decode("utf-8")
        response = (
            '{"task_id":"%s","cell_id":"%s-node","route":"network","status":"executed",'
            '"region":"%s","notes":["network tissue executed"],"resource_budget":1.0,"stress_level":0.2}'
        ) % (payload.split('"task_id": "')[1].split('"')[0], self.region, self.region)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))

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
