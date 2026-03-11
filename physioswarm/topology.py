from __future__ import annotations

from collections import defaultdict, deque


class TissueTopology:
    def __init__(self) -> None:
        self._adjacency: dict[str, set[str]] = defaultdict(set)
        self._placements: dict[str, str] = {}

    def connect(self, left: str, right: str) -> None:
        self._adjacency[left].add(right)
        self._adjacency[right].add(left)
        self._adjacency[left].add(left)
        self._adjacency[right].add(right)

    def place(self, cell_id: str, region: str) -> None:
        self._placements[cell_id] = region
        self._adjacency[region].add(region)

    def region_for(self, cell_id: str) -> str:
        return self._placements.get(cell_id, "core")

    def reachable_regions(self, origin: str, hops: int = 1) -> set[str]:
        self._adjacency[origin].add(origin)
        queue: deque[tuple[str, int]] = deque([(origin, 0)])
        seen = {origin}
        while queue:
            region, distance = queue.popleft()
            if distance >= hops:
                continue
            for neighbor in self._adjacency.get(region, {region}):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, distance + 1))
        return seen

    def candidate_cells(self, origin: str, hops: int = 1) -> list[str]:
        regions = self.reachable_regions(origin, hops=hops)
        return [cell_id for cell_id, region in self._placements.items() if region in regions]

    def snapshot(self) -> dict[str, object]:
        return {
            "regions": {region: sorted(neighbors) for region, neighbors in self._adjacency.items()},
            "placements": dict(self._placements),
        }
