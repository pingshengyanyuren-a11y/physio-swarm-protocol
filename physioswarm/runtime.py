from __future__ import annotations

from dataclasses import asdict

from .cells import BaseCell
from .organs import EndocrineSystem, ImmuneSystem, MetabolicSystem, NervousSystem
from .signal_bus import SignalBus
from .types import CellState, ControlSignal, ExecutionArtifact, HomeostasisState, TaskSignal


class PhysioSwarmRuntime:
    def __init__(self, cells: list[BaseCell]) -> None:
        self.cells = {cell.state.cell_id: cell for cell in cells}
        self.state = HomeostasisState()
        self.endocrine = EndocrineSystem()
        self.metabolic = MetabolicSystem()
        self.nervous = NervousSystem()
        self.immune = ImmuneSystem()
        self.signal_bus = SignalBus()
        self.signal_history: list[dict[str, object]] = []
        for cell_id in self.cells:
            self.signal_bus.subscribe("endocrine", cell_id)
            self.signal_bus.subscribe("immune", cell_id)

    def cell_state(self, cell_id: str) -> CellState:
        return self.cells[cell_id].state

    def snapshot(self) -> dict[str, dict[str, float | bool | str | int]]:
        return {cell_id: asdict(cell.state) for cell_id, cell in self.cells.items()}

    def handle(self, task: TaskSignal) -> ExecutionArtifact:
        mean_load = sum(cell.state.load for cell in self.cells.values()) / max(len(self.cells), 1)
        self.state = self.endocrine.regulate(self.state, task, active_load=mean_load)
        endocrine_signal = ControlSignal(channel="endocrine", payload={"stress": self.state.stress_level})
        endocrine_recipients = self.signal_bus.emit(endocrine_signal)
        self.signal_history.append({"signal": asdict(endocrine_signal), "recipients": endocrine_recipients})

        route, selected = self.nervous.route(task, {cell_id: cell.state for cell_id, cell in self.cells.items()})
        cell = self.cells[selected.cell_id]
        updated_state = self.metabolic.consume(cell.state, task)
        cell.state = updated_state
        _, status, notes = cell.execute(task, self.state)
        cell.state = self.immune.assess(cell.state, status)

        if cell.state.quarantined:
            immune_signal = ControlSignal(channel="immune", payload={"quarantine": True}, target=cell.state.cell_id)
            immune_recipients = self.signal_bus.emit(immune_signal)
            self.signal_history.append({"signal": asdict(immune_signal), "recipients": immune_recipients})
            notes = [*notes, "immune quarantine triggered"]

        artifact = ExecutionArtifact(
            task_id=task.task_id,
            cell_id=cell.state.cell_id,
            route=route,
            status=status if not cell.state.quarantined else "quarantined",
            notes=notes,
            resource_budget=self.state.resource_budget,
            stress_level=self.state.stress_level,
        )
        return artifact
