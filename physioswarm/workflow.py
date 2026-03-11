from __future__ import annotations

from dataclasses import dataclass

from .types import TaskSignal


@dataclass(slots=True)
class WorkflowStage:
    name: str
    objective: str
    urgency: float
    noise: float
    complexity: float

    def to_task(self, index: int) -> TaskSignal:
        return TaskSignal(
            task_id=f"{self.name}-{index}",
            objective=self.objective,
            urgency=self.urgency,
            noise=self.noise,
            complexity=self.complexity,
            tags=(self.name,),
        )


@dataclass(slots=True)
class WorkflowPlan:
    name: str
    stages: list[WorkflowStage]
