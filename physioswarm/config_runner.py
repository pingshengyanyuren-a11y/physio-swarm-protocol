from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from .cells import ReflexCell, ResearchCell
from .registry import OrganRegistry
from .runtime import PhysioSwarmRuntime
from .workflow import WorkflowPlan, WorkflowStage


@dataclass(slots=True)
class ConfigBundle:
    plan: WorkflowPlan
    cells: list[object]
    reserve_cells: list[object]


def _default_registry() -> OrganRegistry:
    registry = OrganRegistry()
    registry.register(
        "reflex_arc",
        lambda cell_id, reliability=0.95, region="core": ReflexCell(cell_id, reliability, region=region),
    )
    registry.register(
        "cortex",
        lambda cell_id, reliability=0.9, region="core": ResearchCell(cell_id, reliability, region=region),
    )
    return registry


def load_plan_from_toml(path: Path) -> ConfigBundle:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    plan = WorkflowPlan(
        name=str(data["name"]),
        stages=[
            WorkflowStage(
                name=str(stage["name"]),
                objective=str(stage["objective"]),
                urgency=float(stage["urgency"]),
                noise=float(stage["noise"]),
                complexity=float(stage["complexity"]),
            )
            for stage in data.get("stages", [])
        ],
    )
    registry = _default_registry()
    cells = registry.build_many(list(data.get("cells", [])))
    reserve_cells = registry.build_many(list(data.get("reserve_cells", [])))
    return ConfigBundle(plan=plan, cells=cells, reserve_cells=reserve_cells)


def run_configured_workflow(path: Path) -> dict[str, object]:
    bundle = load_plan_from_toml(path)
    runtime = PhysioSwarmRuntime(cells=bundle.cells, reserve_cells=bundle.reserve_cells)
    return runtime.run_plan(bundle.plan)
