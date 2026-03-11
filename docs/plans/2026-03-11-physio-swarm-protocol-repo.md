# Physiological Swarm Protocol Repository Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone repository for a physiological multi-agent framework and skill, separate from the benchmark repository.

**Architecture:** Create a protocol-first runtime with explicit signals, organ controllers, cell adapters, and a runnable workflow example. Package the same system as a Codex skill that tells agents how to design organism-style swarms instead of role-play organizations.

**Tech Stack:** Python 3.11, standard library, `unittest`, GitHub Actions, markdown skill files.

---

### Task 1: Protocol primitives and signal bus

**Files:**
- Create: `physioswarm/types.py`
- Create: `physioswarm/signal_bus.py`
- Create: `tests/test_types.py`
- Create: `tests/test_signal_bus.py`

### Task 2: Organ systems and runtime

**Files:**
- Create: `physioswarm/organs.py`
- Create: `physioswarm/runtime.py`
- Create: `physioswarm/cells.py`
- Create: `tests/test_runtime.py`

### Task 3: Demo workflows and adapter surface

**Files:**
- Create: `physioswarm/adapters.py`
- Create: `examples/research_assistant_demo.py`
- Create: `tests/test_demo.py`

### Task 4: Skill packaging and repository docs

**Files:**
- Create: `skills/physio-swarm-architect/SKILL.md`
- Create: `skills/physio-swarm-architect/references/protocol.md`
- Create: `skills/physio-swarm-architect/references/runtime.md`
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `.github/workflows/ci.yml`
- Create: `tests/test_skill.py`

### Task 5: Verification and publishing

**Files:**
- Verify all tests
- Initialize git repo
- Publish public GitHub repo
