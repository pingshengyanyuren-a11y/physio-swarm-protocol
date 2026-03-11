from __future__ import annotations

from .adapters import BaseAdapter, ReflexAdapter, ResearchAdapter
from .types import CellState, HomeostasisState, TaskSignal


class BaseCell:
    def __init__(self, state: CellState, adapter: BaseAdapter) -> None:
        self.state = state
        self.adapter = adapter

    def execute(self, task: TaskSignal, organism_state: HomeostasisState) -> tuple[CellState, str, list[str]]:
        result = self.adapter.run(task, organism_state)
        return self.state, result.status, result.notes


class ReflexCell(BaseCell):
    def __init__(
        self,
        cell_id: str,
        reliability: float = 0.95,
        adapter: BaseAdapter | None = None,
        region: str = "core",
    ) -> None:
        super().__init__(
            CellState(cell_id=cell_id, organ="reflex_arc", region=region, reliability=reliability, energy=0.92),
            adapter or ReflexAdapter(),
        )


class ResearchCell(BaseCell):
    def __init__(
        self,
        cell_id: str,
        reliability: float = 0.9,
        adapter: BaseAdapter | None = None,
        region: str = "core",
    ) -> None:
        super().__init__(
            CellState(cell_id=cell_id, organ="cortex", region=region, reliability=reliability, energy=0.86),
            adapter or ResearchAdapter(),
        )
