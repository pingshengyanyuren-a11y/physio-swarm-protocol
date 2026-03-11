# Physio Swarm Protocol

> A standalone physiological multi-agent framework and skill package.

This repository does not model a software team. It models an organism.

The runtime centers on:

- topology-first tissue neighborhoods
- endocrine global regulation
- circulatory regional resource control
- metabolic energy and load control
- nervous fast-lane routing
- immune quarantine and hazard memory
- explicit signal buses and cell state
- remote LLM provider adapters
- vector-based latent communication with local resonance
- adaptive latent learning
- continuous field diffusion and decay
- durable memory, trust adaptation, and immune patterns
- SQLite-backed scheduling and persistence
- distributed tissue execution
- networked tissue execution across remote nodes
- cluster registry, health checks, and failover
- runnable tissue node server
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

## Remote Provider

The framework now supports real remote provider execution through an OpenAI-compatible adapter surface.

Set:

```powershell
$env:PHYSIOSWARM_LLM_BASE_URL="https://your-provider.example"
$env:PHYSIOSWARM_LLM_API_KEY="..."
$env:PHYSIOSWARM_LLM_MODEL="gpt-4.1-mini"
```

Then build a `RemoteLLMAdapter` directly or via `RemoteLLMAdapter.from_env()`.

## Core Modules

- `physioswarm/types.py`
- `physioswarm/topology.py`
- `physioswarm/latent_model.py`
- `physioswarm/signal_bus.py`
- `physioswarm/vector_bus.py`
- `physioswarm/cells.py`
- `physioswarm/adapters.py`
- `physioswarm/distributed.py`
- `physioswarm/memory.py`
- `physioswarm/registry.py`
- `physioswarm/organs.py`
- `physioswarm/scheduler.py`
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
- tissue topology and local adjacency
- local latent propagation with resonance thresholds
- adaptive latent learning
- contrastive latent learning
- continuous regional field dynamics
- regional homeostasis and circulation snapshots
- event persistence and replay
- networked provider execution
- durable task scheduling
- latent vector signaling
- distributed tissue execution
- network tissue execution across remote endpoints
- cluster registry and healthy-endpoint resolution
- node-level failover
- runnable HTTP tissue node server
- memory recall, trust curriculum, and immune hazard memory
- reserve-cell substitution
- quarantine and recovery
- stage-based workflow execution

It still does not claim to be a full production agent platform, but it is no longer organized around flat global workers and transient control only.
