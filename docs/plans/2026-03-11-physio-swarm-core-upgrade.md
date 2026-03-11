# Physio Swarm Core Upgrade Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add real remote provider execution, durable memory and trust adaptation, vector-based signaling, and persistent scheduling to the physiological swarm framework.

**Architecture:** Keep the existing physiological runtime as the orchestration kernel, then attach four new subsystems: a networked provider adapter, a SQLite-backed memory graph with trust updates, a vector communication bus with similarity search, and a durable task scheduler backed by SQLite. The runtime remains the composition point and exposes the new surfaces through minimal, explicit interfaces.

**Tech Stack:** Python 3.10+, stdlib (`sqlite3`, `urllib`, `json`, `threading`, `datetime`, `http.server`, `tomllib`), optional `numpy` for vector math if already available, `unittest`

---

### Task 1: Add failing tests for remote provider execution

**Files:**
- Modify: `D:\physio-swarm-protocol\tests\test_provider_adapter.py`
- Test: `D:\physio-swarm-protocol\tests\test_provider_adapter.py`

**Step 1: Write the failing test**
- Add a local HTTP server fixture that simulates an OpenAI-compatible `/v1/chat/completions` endpoint.
- Add a test asserting a remote adapter sends the request, parses the response, and returns provider-backed notes.

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_provider_adapter -v`
Expected: FAIL because `RemoteLLMAdapter` does not exist.

**Step 3: Write minimal implementation**
- Add a networked adapter that performs real HTTP requests with bearer auth and OpenAI-compatible JSON payloads.

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_provider_adapter -v`
Expected: PASS

### Task 2: Add failing tests for durable memory graph and trust curriculum

**Files:**
- Create: `D:\physio-swarm-protocol\tests\test_memory.py`
- Test: `D:\physio-swarm-protocol\tests\test_memory.py`

**Step 1: Write the failing test**
- Add tests asserting:
  - task/artifact writes become retrievable memories
  - trust scores decay on failure and recover on success
  - related memory can be recalled for a new task

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_memory -v`
Expected: FAIL because `memory.py` does not exist.

**Step 3: Write minimal implementation**
- Add a SQLite-backed memory graph and trust policy with recall/query helpers.

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_memory -v`
Expected: PASS

### Task 3: Add failing tests for vector communication

**Files:**
- Create: `D:\physio-swarm-protocol\tests\test_vector_bus.py`
- Test: `D:\physio-swarm-protocol\tests\test_vector_bus.py`

**Step 1: Write the failing test**
- Add tests asserting:
  - text objectives can be encoded into vectors
  - vector messages can be broadcast and stored
  - nearest-neighbor lookup returns semantically closest prior messages

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_vector_bus -v`
Expected: FAIL because `vector_bus.py` does not exist.

**Step 3: Write minimal implementation**
- Add a vector codec and vector signal bus with cosine similarity recall.

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_vector_bus -v`
Expected: PASS

### Task 4: Add failing tests for persistent scheduler

**Files:**
- Create: `D:\physio-swarm-protocol\tests\test_scheduler.py`
- Test: `D:\physio-swarm-protocol\tests\test_scheduler.py`

**Step 1: Write the failing test**
- Add tests asserting:
  - due tasks are persisted to SQLite and claimable across scheduler instances
  - running pending tasks invokes the runtime and marks tasks completed

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_scheduler -v`
Expected: FAIL because `scheduler.py` does not exist.

**Step 3: Write minimal implementation**
- Add durable task queue and execution loop with replayable records.

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_scheduler -v`
Expected: PASS

### Task 5: Wire the new subsystems into runtime and docs

**Files:**
- Modify: `D:\physio-swarm-protocol\physioswarm\runtime.py`
- Modify: `D:\physio-swarm-protocol\physioswarm\adapters.py`
- Create: `D:\physio-swarm-protocol\physioswarm\memory.py`
- Create: `D:\physio-swarm-protocol\physioswarm\vector_bus.py`
- Create: `D:\physio-swarm-protocol\physioswarm\scheduler.py`
- Modify: `D:\physio-swarm-protocol\physioswarm\__init__.py`
- Modify: `D:\physio-swarm-protocol\README.md`
- Modify: `D:\physio-swarm-protocol\skills\physio-swarm-architect\SKILL.md`
- Modify: `D:\physio-swarm-protocol\skills\physio-swarm-architect\references\runtime.md`
- Modify: `D:\physio-swarm-protocol\docs\SELF_REVIEW.md`

**Step 1: Write failing integration assertions**
- Extend runtime tests to assert memory writes, trust adaptation, vector signal history, and scheduler-driven execution.

**Step 2: Run targeted tests to verify they fail**

Run: `python -m unittest tests.test_runtime -v`
Expected: FAIL on missing integration behavior.

**Step 3: Write minimal implementation**
- Inject optional stores/buses into runtime.
- Persist execution and signal data to SQLite.
- Update docs to reflect the mature skill surface.

**Step 4: Run full verification**

Run: `python -m unittest discover -s .\tests -v`
Expected: PASS

Run: `python .\scripts\run_workflow.py .\examples\workflows\research-assistant.toml`
Expected: PASS with artifacts and final state output

Run: `python -m pip install -e .`
Expected: PASS

### Task 6: Publish and verify remote health

**Files:**
- Modify: `D:\physio-swarm-protocol\docs\releases\v0.1.3.md`

**Step 1: Prepare release notes**
- Summarize provider, memory, vector, and scheduler additions.

**Step 2: Push and verify**

Run: `git status --short --branch`
Expected: local changes only for this feature

Run: `git add ... && git commit -m "feat: add durable swarm intelligence subsystems"`
Expected: commit created

Run: `git push origin main`
Expected: remote updated

Run: `gh run list --limit 5`
Expected: latest workflow reaches `success`
