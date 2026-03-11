---
name: physio-swarm-architect
description: Use when designing or implementing a multi-agent framework as a physiological organism rather than a human organization. Triggers for endocrine global control, metabolic budget management, nervous fast lanes, immune quarantine, signal buses, cell state schemas, and organism-style orchestration kernels.
---

# Physio Swarm Architect

Treat the system as an organism with organs and cells.

## Core Organs

- `endocrine`: system-wide slow control signals
- `metabolic`: token, energy, and fatigue budgets
- `nervous`: fast routing and local reflex
- `immune`: anomaly detection, quarantine, and recovery

## Workflow

1. Define the global homeostasis variables.
2. Define the cell state model.
3. Separate broadcast signals from targeted signals.
4. Route urgent low-noise tasks through nervous fast lanes.
5. Let endocrine state contract or relax system budgets.
6. Let immune logic quarantine repeated failures.
7. Return structured artifacts rather than pure transcripts.

## Runtime

Start from:

- `physioswarm/types.py`
- `physioswarm/signal_bus.py`
- `physioswarm/organs.py`
- `physioswarm/runtime.py`
- `examples/research_assistant_demo.py`

Read:

- `references/protocol.md`
- `references/runtime.md`
