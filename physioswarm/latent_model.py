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


class ContrastiveLatentModel(AdaptiveLatentModel):
    def __init__(self, dimensions: int = 64, learning_rate: float = 0.28, margin: float = 0.15) -> None:
        super().__init__(dimensions=dimensions, learning_rate=learning_rate)
        self.margin = margin
        self._context_bias: dict[str, list[float]] = defaultdict(lambda: [0.0] * self.dimensions)

    def encode(self, text: str, context: str | None = None) -> list[float]:
        vector = super().encode(text)
        if context is None:
            return vector
        bias = self._context_bias[context]
        return [value + (adjustment * 0.25) for value, adjustment in zip(vector, bias)]

    def observe_pair(self, left: str, right: str, positive: bool, context: str) -> None:
        left_vector = self.encode(left, context=context)
        right_vector = self.encode(right, context=context)
        if positive:
            target = [
                left_value + (self.learning_rate * (right_value - left_value))
                for left_value, right_value in zip(left_vector, right_vector)
            ]
            self._context_bias[context] = [
                (1.0 - self.learning_rate) * value + (self.learning_rate * goal)
                for value, goal in zip(self._context_bias[context], target)
            ]
            self.observe(left, label=context)
            self.observe(right, label=context)
            return

        self._context_bias[context] = [
            value - (self.learning_rate * (left_value + right_value) * 0.5)
            for value, left_value, right_value in zip(self._context_bias[context], left_vector, right_vector)
        ]
        for token in left.lower().split():
            self._token_bias[token] = [
                weight + (self.learning_rate * (left_value - right_value))
                for weight, left_value, right_value in zip(self._token_bias[token], left_vector, right_vector)
            ]
        for token in right.lower().split():
            self._token_bias[token] = [
                weight - (self.learning_rate * (left_value - right_value))
                for weight, left_value, right_value in zip(self._token_bias[token], left_vector, right_vector)
            ]
        self.observe(left, label=context)
        self.observe(right, label=f"{context}:other")

    def similarity(self, left: str, right: str, context: str | None = None) -> float:
        return cosine_similarity(self.encode(left, context=context), self.encode(right, context=context))
