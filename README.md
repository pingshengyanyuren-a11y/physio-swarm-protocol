# Physio Swarm Protocol

> A standalone physiological multi-agent framework and skill package.

This repository does not model a software team. It models an organism.

The runtime centers on:

- endocrine global regulation
- metabolic energy and load control
- nervous fast-lane routing
- immune quarantine
- explicit signal buses and cell state

## Quickstart

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python .\examples\research_assistant_demo.py
python -m unittest discover -s .\tests -v
```

## Core Modules

- `physioswarm/types.py`
- `physioswarm/signal_bus.py`
- `physioswarm/cells.py`
- `physioswarm/organs.py`
- `physioswarm/runtime.py`

## Skill

The bundled skill lives in:

- `skills/physio-swarm-architect/SKILL.md`

It is meant to guide future Codex sessions toward organism-style swarm design rather than role-play organizations.
