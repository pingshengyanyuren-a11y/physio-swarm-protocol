from __future__ import annotations

from dataclasses import dataclass, field


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(value, upper))


@dataclass(slots=True)
class HomeostasisState:
    stress_level: float = 0.2
    risk_level: float = 0.2
    resource_budget: float = 1.0
    energy_budget: float = 1.0
    exploration_level: float = 0.45
    toxicity_level: float = 0.0


@dataclass(slots=True)
class TaskSignal:
    task_id: str
    objective: str
    urgency: float
    noise: float
    complexity: float
    tags: tuple[str, ...] = ()

    def qualifies_for_fast_lane(self) -> bool:
        return self.urgency >= 0.8 and self.noise <= 0.25 and self.complexity <= 0.35


@dataclass(slots=True)
class ControlSignal:
    channel: str
    payload: dict[str, float | bool | str]
    source: str = "organism"
    target: str | None = None


@dataclass(slots=True)
class CellState:
    cell_id: str
    organ: str
    energy: float = 1.0
    load: float = 0.0
    reliability: float = 1.0
    health: float = 1.0
    quarantined: bool = False
    recent_failures: int = 0

    @property
    def is_fatigued(self) -> bool:
        return self.energy <= 0.25 or self.load >= 0.85


@dataclass(slots=True)
class ExecutionArtifact:
    task_id: str
    cell_id: str
    route: str
    status: str
    notes: list[str] = field(default_factory=list)
    resource_budget: float = 1.0
    stress_level: float = 0.2
