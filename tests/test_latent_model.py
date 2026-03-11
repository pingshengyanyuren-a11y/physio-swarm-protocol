from __future__ import annotations

import unittest

from physioswarm.latent_model import AdaptiveLatentModel, ContrastiveLatentModel


class LatentModelTest(unittest.TestCase):
    def test_adaptive_latent_model_strengthens_similarity_after_training(self) -> None:
        model = AdaptiveLatentModel(dimensions=32)
        before = model.similarity("evidence synthesis", "evidence drafting")

        model.observe("evidence synthesis", label="research")
        model.observe("evidence drafting", label="research")
        after = model.similarity("evidence synthesis", "evidence drafting")

        self.assertGreater(after, before)
        self.assertGreater(after, 0.4)

    def test_contrastive_latent_model_separates_positive_and_negative_pairs(self) -> None:
        model = ContrastiveLatentModel(dimensions=32)
        before_positive = model.similarity("evidence synthesis", "evidence drafting")
        before_negative = model.similarity("evidence synthesis", "malware payload")

        model.observe_pair("evidence synthesis", "evidence drafting", positive=True, context="research")
        model.observe_pair("evidence synthesis", "malware payload", positive=False, context="research")

        after_positive = model.similarity("evidence synthesis", "evidence drafting")
        after_negative = model.similarity("evidence synthesis", "malware payload")

        self.assertGreater(after_positive, before_positive)
        self.assertLess(after_negative, before_negative)
