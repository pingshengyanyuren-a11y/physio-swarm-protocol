from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field

from .embeddings import cosine_similarity, embed_text


@dataclass(slots=True)
class VectorSignal:
    channel: str
    objective: str
    source: str
    task_id: str | None = None
    target: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)
    vector: list[float] | None = None


class SemanticVectorBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[str]] = defaultdict(set)
        self.history: list[dict[str, object]] = []

    def subscribe(self, subscriber_id: str, channel: str = "latent") -> None:
        self._subscribers[channel].add(subscriber_id)

    def broadcast(self, signal: VectorSignal) -> list[str]:
        vector = signal.vector or embed_text(signal.objective)
        if signal.target is None:
            recipients = sorted(self._subscribers.get(signal.channel, set()))
        else:
            recipients = [
                subscriber
                for subscriber in sorted(self._subscribers.get(signal.channel, set()))
                if subscriber == signal.target
            ]
        self.history.append(
            {
                "channel": signal.channel,
                "objective": signal.objective,
                "source": signal.source,
                "task_id": signal.task_id,
                "target": signal.target,
                "metadata": dict(signal.metadata),
                "vector": vector,
                "recipients": recipients,
            }
        )
        return recipients

    def recall(self, objective: str, limit: int = 3) -> list[dict[str, object]]:
        query = embed_text(objective)
        matches: list[dict[str, object]] = []
        for record in self.history:
            score = cosine_similarity(query, list(record["vector"]))
            matches.append(
                {
                    "channel": record["channel"],
                    "objective": record["objective"],
                    "source": record["source"],
                    "task_id": record["task_id"],
                    "metadata": dict(record["metadata"]),
                    "score": score,
                }
            )
        matches.sort(key=lambda item: item["score"], reverse=True)
        return matches[:limit]
