# Physio Swarm Protocol

> A standalone physiological multi-agent framework and skill package.

This repository does not model a software team. It models an organism.

The runtime centers on:

- endocrine global regulation
- metabolic energy and load control
- nervous fast-lane routing
- immune quarantine
- explicit signal buses and cell state
- reserve-cell promotion and recovery
- workflow-stage execution through a lightweight DSL

## Quickstart

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python .\examples\research_assistant_demo.py
python .\scripts\run_workflow.py .\examples\workflows\research-assistant.toml
python -m unittest discover -s .\tests -v
```

## Core Modules

- `physioswarm/types.py`
- `physioswarm/signal_bus.py`
- `physioswarm/cells.py`
- `physioswarm/registry.py`
- `physioswarm/organs.py`
- `physioswarm/config_runner.py`
- `physioswarm/runtime.py`
- `physioswarm/workflow.py`

## Skill

The bundled skill lives in:

- `skills/physio-swarm-architect/SKILL.md`

It is meant to guide future Codex sessions toward organism-style swarm design rather than role-play organizations.

## Current Scope

This repository is now strong enough to express:

- organ-level control
- signal broadcasting
- event persistence and replay
- provider-style adapter injection
- reserve-cell substitution
- quarantine and recovery
- stage-based workflow execution

It still does not claim to be a production-ready agent platform or full LLM orchestration stack.
