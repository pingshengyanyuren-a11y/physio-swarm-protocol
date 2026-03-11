from __future__ import annotations

from dataclasses import replace

from .types import CellState, HomeostasisState, TaskSignal, clamp


class EndocrineSystem:
    def regulate(self, state: HomeostasisState, task: TaskSignal, active_load: float) -> HomeostasisState:
        queue_pressure = (task.urgency * 0.35) + (task.complexity * 0.35) + (active_load * 0.3)
        stress = clamp(state.stress_level + (queue_pressure * 0.14) + (task.noise * 0.05))
        risk = clamp(state.risk_level + (task.noise * 0.18) + (task.complexity * 0.07))
        resource_budget = clamp(state.resource_budget - (queue_pressure * 0.12))
        energy_budget = clamp(state.energy_budget - (task.complexity * 0.06))
        exploration = clamp(state.exploration_level - (stress * 0.15) - (risk * 0.08))
        toxicity = clamp(state.toxicity_level + (task.noise * 0.1))
        return HomeostasisState(
            stress_level=stress,
            risk_level=risk,
            resource_budget=resource_budget,
            energy_budget=energy_budget,
            exploration_level=exploration,
            toxicity_level=toxicity,
        )


class MetabolicSystem:
    def consume(self, cell: CellState, task: TaskSignal) -> CellState:
        energy = clamp(cell.energy - (0.05 + (task.complexity * 0.08)))
        load = clamp(cell.load + (0.05 + (task.urgency * 0.06)))
        health = clamp(cell.health - (0.04 if cell.is_fatigued else 0.015))
        return replace(cell, energy=energy, load=load, health=health)


class NervousSystem:
    def route(
        self,
        task: TaskSignal,
        cells: dict[str, CellState],
        trust_scores: dict[str, float] | None = None,
    ) -> tuple[str, CellState]:
        eligible = [cell for cell in cells.values() if not cell.quarantined]
        trust_scores = trust_scores or {}
        if task.qualifies_for_fast_lane():
            reflex = sorted(
                [cell for cell in eligible if cell.organ == "reflex_arc"],
                key=lambda cell: trust_scores.get(cell.cell_id, cell.reliability),
                reverse=True,
            )
            if reflex:
                return "fast_lane", reflex[0]
        cortex = sorted(
            [cell for cell in eligible if cell.organ == "cortex"],
            key=lambda cell: trust_scores.get(cell.cell_id, cell.reliability),
            reverse=True,
        )
        if cortex:
            return "deliberative", cortex[0]
        return "fallback", eligible[0]


class ImmuneSystem:
    def assess(self, cell: CellState, status: str) -> CellState:
        if status == "failed":
            failures = cell.recent_failures + 1
            reliability = clamp(cell.reliability - 0.12)
            quarantined = failures >= 2 or reliability <= 0.2
            return replace(cell, recent_failures=failures, reliability=reliability, quarantined=quarantined)
        failures = max(0, cell.recent_failures - 1)
        reliability = clamp(cell.reliability + 0.02)
        return replace(cell, recent_failures=failures, reliability=reliability)
