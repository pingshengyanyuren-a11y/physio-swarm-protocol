from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .embeddings import cosine_similarity, embed_text
from .topology import TissueTopology


@dataclass(slots=True)
class VectorSignal:
    channel: str
    objective: str
    source: str
    task_id: str | None = None
    target: str | None = None
    region: str = "core"
    hops: int = 1
    activation_threshold: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)
    vector: list[float] | None = None


class SemanticVectorBus:
    def __init__(self, topology: TissueTopology | None = None) -> None:
        self._subscribers: dict[str, set[str]] = defaultdict(set)
        self._subscriber_regions: dict[str, str] = {}
        self._region_fields: dict[str, list[float]] = {}
        self.topology = topology
        self.history: list[dict[str, object]] = []

    def subscribe(self, subscriber_id: str, channel: str = "latent", region: str = "core") -> None:
        self._subscribers[channel].add(subscriber_id)
        self._subscriber_regions[subscriber_id] = region

    def broadcast(self, signal: VectorSignal) -> list[str]:
        vector = signal.vector or embed_text(signal.objective)
        subscribers = sorted(self._subscribers.get(signal.channel, set()))
        if signal.target is not None:
            recipients = [subscriber for subscriber in subscribers if subscriber == signal.target]
        elif self.topology is None:
            recipients = subscribers
        else:
            reachable = self.topology.reachable_regions(signal.region, hops=signal.hops)
            recipients = []
            for subscriber in subscribers:
                region = self._subscriber_regions.get(subscriber, "core")
                if region not in reachable:
                    continue
                if region == signal.region:
                    recipients.append(subscriber)
                    continue
                field = self._region_fields.get(region)
                resonance = cosine_similarity(vector, field) if field is not None else 0.0
                if resonance >= signal.activation_threshold:
                    recipients.append(subscriber)
        self._merge_region_field(signal.region, vector)
        for subscriber in recipients:
            region = self._subscriber_regions.get(subscriber, signal.region)
            if region != signal.region:
                self._merge_region_field(region, vector, attenuation=0.5)
        self.history.append(
            {
                "channel": signal.channel,
                "objective": signal.objective,
                "source": signal.source,
                "task_id": signal.task_id,
                "target": signal.target,
                "region": signal.region,
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
                    "region": record["region"],
                    "metadata": dict(record["metadata"]),
                    "score": score,
                }
            )
        matches.sort(key=lambda item: item["score"], reverse=True)
        return matches[:limit]

    def _merge_region_field(self, region: str, vector: list[float], attenuation: float = 1.0) -> None:
        scaled = [value * attenuation for value in vector]
        existing = self._region_fields.get(region)
        if existing is None:
            self._region_fields[region] = list(scaled)
            return
        self._region_fields[region] = [
            (left * 0.7) + (right * 0.3)
            for left, right in zip(existing, scaled)
        ]
