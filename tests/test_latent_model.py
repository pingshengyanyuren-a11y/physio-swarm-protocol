from __future__ import annotations

import unittest

from physioswarm.latent_model import AdaptiveLatentModel


class LatentModelTest(unittest.TestCase):
    def test_adaptive_latent_model_strengthens_similarity_after_training(self) -> None:
        model = AdaptiveLatentModel(dimensions=32)
        before = model.similarity("evidence synthesis", "evidence drafting")

        model.observe("evidence synthesis", label="research")
        model.observe("evidence drafting", label="research")
        after = model.similarity("evidence synthesis", "evidence drafting")

        self.assertGreater(after, before)
        self.assertGreater(after, 0.4)
