from __future__ import annotations

import unittest

from physioswarm.latent_model import AdaptiveLatentModel
from physioswarm.topology import TissueTopology
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

    def test_vector_bus_uses_local_resonance_for_neighbor_propagation(self) -> None:
        topology = TissueTopology()
        topology.connect("cortex", "hippocampus")
        topology.place("cortex-1", "cortex")
        topology.place("hippo-1", "hippocampus")
        topology.place("liver-1", "liver")
        bus = SemanticVectorBus(topology=topology)
        bus.subscribe("cortex-1", region="cortex")
        bus.subscribe("hippo-1", region="hippocampus")
        bus.subscribe("liver-1", region="liver")

        bus.broadcast(
            VectorSignal(
                channel="latent",
                objective="evidence synthesis memory trace",
                source="hippo-1",
                region="hippocampus",
            )
        )
        recipients = bus.broadcast(
            VectorSignal(
                channel="latent",
                objective="evidence synthesis relay",
                source="cortex-1",
                region="cortex",
                hops=1,
                activation_threshold=0.2,
            )
        )

        self.assertIn("cortex-1", recipients)
        self.assertIn("hippo-1", recipients)
        self.assertNotIn("liver-1", recipients)

    def test_vector_bus_diffuses_and_decays_continuous_region_fields(self) -> None:
        topology = TissueTopology()
        topology.connect("cortex", "hippocampus")
        model = AdaptiveLatentModel(dimensions=32)
        bus = SemanticVectorBus(topology=topology, latent_model=model)
        bus.subscribe("cortex-1", region="cortex")
        bus.subscribe("hippo-1", region="hippocampus")

        bus.broadcast(
            VectorSignal(
                channel="latent",
                objective="encode evidence memory",
                source="cortex-1",
                region="cortex",
            )
        )
        initial = bus.field_strength("cortex")
        bus.tick(decay=0.8, diffusion=0.25)
        cortex_strength = bus.field_strength("cortex")
        hippo_strength = bus.field_strength("hippocampus")

        self.assertLess(cortex_strength, initial)
        self.assertGreater(hippo_strength, 0.0)
