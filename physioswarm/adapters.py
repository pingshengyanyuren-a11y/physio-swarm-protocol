from __future__ import annotations

from dataclasses import dataclass

from .types import HomeostasisState, TaskSignal


@dataclass(slots=True)
class AdapterResult:
    status: str
    notes: list[str]


class BaseAdapter:
    def run(self, task: TaskSignal, state: HomeostasisState) -> AdapterResult:
        raise NotImplementedError


class ReflexAdapter(BaseAdapter):
    def run(self, task: TaskSignal, state: HomeostasisState) -> AdapterResult:
        return AdapterResult(
            status="executed",
            notes=[f"reflex action completed for {task.objective}"],
        )


class ResearchAdapter(BaseAdapter):
    def run(self, task: TaskSignal, state: HomeostasisState) -> AdapterResult:
        if task.noise >= 0.9:
            return AdapterResult(
                status="failed",
                notes=[f"research path stalled on noisy input for {task.objective}"],
            )
        mode = "conservative" if state.stress_level >= 0.45 else "exploratory"
        return AdapterResult(
            status="executed",
            notes=[f"research path processed {task.objective} in {mode} mode"],
        )
