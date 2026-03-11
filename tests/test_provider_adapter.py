from __future__ import annotations

import unittest

from physioswarm.adapters import MockLLMAdapter, ProviderRequest
from physioswarm.cells import ResearchCell
from physioswarm.runtime import PhysioSwarmRuntime
from physioswarm.types import TaskSignal


class ProviderAdapterTest(unittest.TestCase):
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
