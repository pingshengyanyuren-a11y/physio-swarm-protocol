from __future__ import annotations

import unittest

from physioswarm.vector_bus import SemanticVectorBus, VectorSignal


class VectorBusTest(unittest.TestCase):
    def test_vector_bus_broadcasts_and_recalls_nearest_messages(self) -> None:
        bus = SemanticVectorBus()
        bus.subscribe("cortex")
        bus.broadcast(
            VectorSignal(
                channel="latent",
                objective="draft evidence synthesis",
                source="cortex-1",
            )
        )
        bus.broadcast(
            VectorSignal(
                channel="latent",
                objective="repair failing test suite",
                source="cortex-2",
            )
        )

        matches = bus.recall("evidence drafting", limit=1)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["source"], "cortex-1")
        self.assertGreater(matches[0]["score"], 0.0)

