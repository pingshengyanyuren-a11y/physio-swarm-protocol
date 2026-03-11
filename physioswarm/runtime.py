from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .cells import BaseCell
from .event_store import EventStore
from .memory import MemoryGraph
from .organs import EndocrineSystem, ImmuneSystem, MetabolicSystem, NervousSystem
from .signal_bus import SignalBus
from .types import CellState, ControlSignal, ExecutionArtifact, HomeostasisState, TaskSignal
from .vector_bus import SemanticVectorBus, VectorSignal


class PhysioSwarmRuntime:
    def __init__(
        self,
        cells: list[BaseCell],
        reserve_cells: list[BaseCell] | None = None,
        event_log_path: Path | None = None,
        memory_graph: MemoryGraph | None = None,
        vector_bus: SemanticVectorBus | None = None,
    ) -> None:
        self.cells = {cell.state.cell_id: cell for cell in cells}
        self.reserve_cells = {cell.state.cell_id: cell for cell in (reserve_cells or [])}
        self.state = HomeostasisState()
        self.endocrine = EndocrineSystem()
        self.metabolic = MetabolicSystem()
        self.nervous = NervousSystem()
        self.immune = ImmuneSystem()
        self.signal_bus = SignalBus()
        self.signal_history: list[dict[str, object]] = []
        self.recovery_pool: set[str] = set()
        self.event_store = EventStore(event_log_path) if event_log_path is not None else None
        self.memory_graph = memory_graph
        self.vector_bus = vector_bus
        for cell_id in [*self.cells.keys(), *self.reserve_cells.keys()]:
            self.signal_bus.subscribe("endocrine", cell_id)
            self.signal_bus.subscribe("immune", cell_id)
            if self.vector_bus is not None:
                self.vector_bus.subscribe(cell_id)

    def cell_state(self, cell_id: str) -> CellState:
        if cell_id in self.cells:
            return self.cells[cell_id].state
        return self.reserve_cells[cell_id].state

    def active_cells(self) -> list[str]:
        return list(self.cells)

    def snapshot(self) -> dict[str, dict[str, float | bool | str | int]]:
        return {cell_id: asdict(cell.state) for cell_id, cell in self.cells.items()}

    def _record_event(self, event_type: str, payload: dict[str, object]) -> None:
        if self.event_store is not None:
            self.event_store.append(event_type, payload)

    def _promote_reserve(self, organ: str) -> None:
        for cell_id, cell in list(self.reserve_cells.items()):
            if cell.state.organ == organ:
                self.cells[cell_id] = cell
                del self.reserve_cells[cell_id]
                return

    def recover_quarantined_cells(self) -> None:
        for cell_id, cell in self.cells.items():
            if cell.state.quarantined:
                cell.state = CellState(
                    cell_id=cell.state.cell_id,
                    organ=cell.state.organ,
                    energy=max(0.55, cell.state.energy),
                    load=0.1,
                    reliability=max(0.5, cell.state.reliability),
                    health=max(0.7, cell.state.health),
                    quarantined=False,
                    recent_failures=0,
                )
                self.recovery_pool.add(cell_id)

    def handle(self, task: TaskSignal) -> ExecutionArtifact:
        mean_load = sum(cell.state.load for cell in self.cells.values()) / max(len(self.cells), 1)
        self.state = self.endocrine.regulate(self.state, task, active_load=mean_load)
        endocrine_signal = ControlSignal(channel="endocrine", payload={"stress": self.state.stress_level})
        endocrine_recipients = self.signal_bus.emit(endocrine_signal)
        signal_record = {"signal": asdict(endocrine_signal), "recipients": endocrine_recipients}
        self.signal_history.append(signal_record)
        self._record_event("signal", signal_record)

        trust_scores = {}
        if self.memory_graph is not None:
            trust_scores = {
                cell_id: self.memory_graph.trust_score(cell_id)
                for cell_id in self.cells
            }
        route, selected = self.nervous.route(
            task,
            {cell_id: cell.state for cell_id, cell in self.cells.items()},
            trust_scores=trust_scores,
        )
        cell = self.cells[selected.cell_id]
        updated_state = self.metabolic.consume(cell.state, task)
        cell.state = updated_state
        _, status, notes = cell.execute(task, self.state)
        cell.state = self.immune.assess(cell.state, status)

        if cell.state.quarantined:
            immune_signal = ControlSignal(channel="immune", payload={"quarantine": True}, target=cell.state.cell_id)
            immune_recipients = self.signal_bus.emit(immune_signal)
            immune_record = {"signal": asdict(immune_signal), "recipients": immune_recipients}
            self.signal_history.append(immune_record)
            self._record_event("signal", immune_record)
            notes = [*notes, "immune quarantine triggered"]
            self._promote_reserve(cell.state.organ)

        artifact = ExecutionArtifact(
            task_id=task.task_id,
            cell_id=cell.state.cell_id,
            route=route,
            status=status if not cell.state.quarantined else "quarantined",
            notes=notes,
            resource_budget=self.state.resource_budget,
            stress_level=self.state.stress_level,
        )
        if self.memory_graph is not None:
            self.memory_graph.store_interaction(task, artifact)
            self.memory_graph.record_outcome(cell.state.cell_id, artifact.status)
        if self.vector_bus is not None:
            recipients = self.vector_bus.broadcast(
                VectorSignal(
                    channel="latent",
                    objective=f"{task.objective} {' '.join(artifact.notes)}".strip(),
                    source=cell.state.cell_id,
                    task_id=task.task_id,
                    metadata={"route": artifact.route, "status": artifact.status},
                )
            )
            vector_record = {
                "signal": {
                    "channel": "latent",
                    "source": cell.state.cell_id,
                    "task_id": task.task_id,
                    "objective": task.objective,
                },
                "recipients": recipients,
            }
            self.signal_history.append(vector_record)
            self._record_event("signal", vector_record)
        self._record_event("artifact", asdict(artifact))
        return artifact

    def run_plan(self, plan) -> dict[str, object]:
        artifacts: list[dict[str, object]] = []
        for index, stage in enumerate(plan.stages, start=1):
            artifact = self.handle(stage.to_task(index))
            record = asdict(artifact)
            record["stage"] = stage.name
            artifacts.append(record)
        return {
            "plan": plan.name,
            "artifacts": artifacts,
            "signals": list(self.signal_history),
            "final_state": asdict(self.state),
            "memory": self.memory_graph.snapshot() if self.memory_graph is not None else {},
        }

    def replay_events(self) -> list[dict[str, object]]:
        if self.event_store is None:
            return []
        return self.event_store.read_all()

    def close(self) -> None:
        if self.memory_graph is not None:
            self.memory_graph.close()
