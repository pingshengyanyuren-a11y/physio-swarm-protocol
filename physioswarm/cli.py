from __future__ import annotations

from dataclasses import asdict

from .runtime import PhysioSwarmRuntime
from .cells import ReflexCell, ResearchCell
from .types import TaskSignal


def run_demo() -> dict[str, object]:
    runtime = PhysioSwarmRuntime(
        cells=[
            ReflexCell("reflex-1"),
            ResearchCell("cortex-1"),
            ResearchCell("cortex-risky", reliability=0.45),
        ]
    )
    tasks = [
        TaskSignal("urgent-stop", "halt runaway loop", urgency=0.96, noise=0.08, complexity=0.2),
        TaskSignal("deep-synthesis", "synthesize literature", urgency=0.55, noise=0.3, complexity=0.82),
        TaskSignal("noisy-review", "review noisy findings", urgency=0.4, noise=0.95, complexity=0.85),
        TaskSignal("noisy-review-2", "review noisy findings again", urgency=0.4, noise=0.95, complexity=0.85),
    ]
    artifacts = [asdict(runtime.handle(task)) for task in tasks]
    return {
        "artifacts": artifacts,
        "signals": list(runtime.signal_history),
        "final_state": asdict(runtime.state),
        "final_cells": runtime.snapshot(),
    }


def main() -> int:
    result = run_demo()
    for artifact in result["artifacts"]:
        print(artifact)
    print("final_state", result["final_state"])
    return 0
