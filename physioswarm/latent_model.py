from __future__ import annotations

from collections import defaultdict

from .embeddings import cosine_similarity, embed_text


class AdaptiveLatentModel:
    def __init__(self, dimensions: int = 64, learning_rate: float = 0.35) -> None:
        self.dimensions = dimensions
        self.learning_rate = learning_rate
        self._label_prototypes: dict[str, list[float]] = {}
        self._token_bias: dict[str, list[float]] = defaultdict(lambda: [0.0] * self.dimensions)

    def encode(self, text: str) -> list[float]:
        base = embed_text(text, dimensions=self.dimensions)
        tokens = text.lower().split()
        if not tokens:
            return base
        bias = [0.0] * self.dimensions
        for token in tokens:
            weights = self._token_bias[token]
            bias = [left + right for left, right in zip(bias, weights)]
        scale = 1.0 / len(tokens)
        return [
            (value + (adjustment * scale))
            for value, adjustment in zip(base, bias)
        ]

    def observe(self, text: str, label: str) -> list[float]:
        vector = self.encode(text)
        prototype = self._label_prototypes.get(label, [0.0] * self.dimensions)
        updated = [
            (1.0 - self.learning_rate) * old + (self.learning_rate * new)
            for old, new in zip(prototype, vector)
        ]
        self._label_prototypes[label] = updated
        for token in text.lower().split():
            self._token_bias[token] = [
                (1.0 - self.learning_rate) * weight + (self.learning_rate * proto)
                for weight, proto in zip(self._token_bias[token], updated)
            ]
        return updated

    def similarity(self, left: str, right: str) -> float:
        return cosine_similarity(self.encode(left), self.encode(right))
