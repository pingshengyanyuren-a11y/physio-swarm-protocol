from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from physioswarm.adapters import MockLLMAdapter, ProviderRequest, RemoteLLMAdapter
from physioswarm.cells import ResearchCell
from physioswarm.runtime import PhysioSwarmRuntime
from physioswarm.types import TaskSignal


class _ProviderHandler(BaseHTTPRequestHandler):
    payload: dict[str, object] | None = None
    auth_header: str | None = None

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length)
        _ProviderHandler.payload = json.loads(body)
        _ProviderHandler.auth_header = self.headers.get("Authorization")
        response = {
            "choices": [
                {
                    "message": {
                        "content": "remote synthesis ready",
                    }
                }
            ]
        }
        encoded = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


class ProviderAdapterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _ProviderHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1)

    def test_mock_llm_adapter_records_provider_specific_execution(self) -> None:
        adapter = MockLLMAdapter(provider_name="mock-gpt")
        response = adapter.run_request(
            ProviderRequest(
                objective="draft literature synthesis",
                mode="conservative",
                tags=("analysis",),
            )
        )

        self.assertEqual(response.status, "executed")
        self.assertIn("mock-gpt", response.notes[0])

    def test_remote_llm_adapter_calls_openai_compatible_endpoint(self) -> None:
        adapter = RemoteLLMAdapter(
            provider_name="remote-gpt",
            base_url=self.base_url,
            api_key="test-key",
            model="demo-model",
        )

        response = adapter.run_request(
            ProviderRequest(
                objective="draft literature synthesis",
                mode="conservative",
                tags=("analysis", "evidence"),
            )
        )

        self.assertEqual(response.status, "executed")
        self.assertIn("remote-gpt", response.notes[0])
        self.assertEqual(_ProviderHandler.auth_header, "Bearer test-key")
        self.assertEqual(_ProviderHandler.payload["model"], "demo-model")
        self.assertIn("draft literature synthesis", json.dumps(_ProviderHandler.payload))

    def test_runtime_accepts_custom_adapter_cells(self) -> None:
        runtime = PhysioSwarmRuntime(
            cells=[ResearchCell("cortex-1", adapter=MockLLMAdapter(provider_name="mock-gpt"))],
        )
        artifact = runtime.handle(
            TaskSignal("deep-1", "draft synthesis", urgency=0.55, noise=0.2, complexity=0.8)
        )

        self.assertIn("mock-gpt", artifact.notes[0])


if __name__ == "__main__":
    unittest.main()
