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


@dataclass(slots=True)
class ProviderRequest:
    objective: str
    mode: str
    tags: tuple[str, ...] = ()


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


class MockLLMAdapter(BaseAdapter):
    def __init__(self, provider_name: str = "mock-llm") -> None:
        self.provider_name = provider_name

    def run_request(self, request: ProviderRequest) -> AdapterResult:
        return AdapterResult(
            status="executed",
            notes=[f"{self.provider_name} completed {request.objective} in {request.mode} mode"],
        )

    def run(self, task: TaskSignal, state: HomeostasisState) -> AdapterResult:
        if task.noise >= 0.9:
            return AdapterResult(
                status="failed",
                notes=[f"{self.provider_name} rejected noisy objective {task.objective}"],
            )
        mode = "conservative" if state.stress_level >= 0.45 else "exploratory"
        return self.run_request(ProviderRequest(objective=task.objective, mode=mode, tags=task.tags))
