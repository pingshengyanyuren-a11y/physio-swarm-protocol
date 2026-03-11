from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib import request

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


class RemoteLLMAdapter(BaseAdapter):
    def __init__(
        self,
        provider_name: str,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(
        cls,
        provider_name: str = "openai-compatible",
        base_url_env: str = "PHYSIOSWARM_LLM_BASE_URL",
        api_key_env: str = "PHYSIOSWARM_LLM_API_KEY",
        model_env: str = "PHYSIOSWARM_LLM_MODEL",
    ) -> "RemoteLLMAdapter":
        return cls(
            provider_name=provider_name,
            base_url=os.environ[base_url_env],
            api_key=os.environ[api_key_env],
            model=os.environ[model_env],
        )

    def run_request(self, request_model: ProviderRequest) -> AdapterResult:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a physiological swarm cell. Return concise operational output "
                        f"for mode={request_model.mode}."
                    ),
                },
                {
                    "role": "user",
                    "content": request_model.objective,
                },
            ],
            "metadata": {"tags": list(request_model.tags), "mode": request_model.mode},
        }
        body = json.dumps(payload).encode("utf-8")
        endpoint = f"{self.base_url}/v1/chat/completions"
        http_request = request.Request(
            endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return AdapterResult(status="executed", notes=[f"{self.provider_name}: {content}"])

    def run(self, task: TaskSignal, state: HomeostasisState) -> AdapterResult:
        if task.noise >= 0.97:
            return AdapterResult(
                status="failed",
                notes=[f"{self.provider_name} refused toxic objective {task.objective}"],
            )
        mode = "conservative" if state.stress_level >= 0.45 else "exploratory"
        return self.run_request(ProviderRequest(objective=task.objective, mode=mode, tags=task.tags))
