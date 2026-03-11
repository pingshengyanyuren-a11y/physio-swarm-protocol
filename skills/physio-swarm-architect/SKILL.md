---
name: physio-swarm-architect
description: Use when designing or implementing a multi-agent framework as a physiological organism rather than a human organization. Triggers for endocrine global control, metabolic budget management, nervous fast lanes, immune quarantine, signal buses, cell state schemas, and organism-style orchestration kernels.
---

# Physio Swarm Architect

Treat the system as an organism with organs and cells.

## Core Organs

- `endocrine`: system-wide slow control signals
- `circulatory`: regional resource flow and local stress
- `metabolic`: token, energy, and fatigue budgets
- `nervous`: fast routing and local reflex
- `immune`: anomaly detection, quarantine, recovery, and hazard memory

## Workflow

1. Define the global homeostasis variables.
2. Define tissue topology and local neighborhood boundaries.
3. Define the cell state model.
4. Separate broadcast signals from targeted signals.
5. Route urgent low-noise tasks through nervous fast lanes.
6. Let endocrine state contract or relax system budgets.
7. Let circulatory state regulate local tissue resources.
8. Let immune logic quarantine repeated failures and retain hazard memory.
9. Attach durable memory and trust adaptation rather than stateless retries.
10. Add latent vector channels for non-linguistic coordination.
11. Return structured artifacts rather than pure transcripts.

## Runtime

Start from:

- `physioswarm/types.py`
- `physioswarm/topology.py`
- `physioswarm/signal_bus.py`
- `physioswarm/vector_bus.py`
- `physioswarm/memory.py`
- `physioswarm/registry.py`
- `physioswarm/organs.py`
- `physioswarm/adapters.py`
- `physioswarm/scheduler.py`
- `physioswarm/config_runner.py`
- `physioswarm/runtime.py`
- `physioswarm/workflow.py`
- `examples/research_assistant_demo.py`
- `scripts/run_workflow.py`

Read:

- `references/protocol.md`
- `references/runtime.md`
