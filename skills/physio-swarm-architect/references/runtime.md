# Runtime Reference

Key modules:

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

Example:

- `examples/research_assistant_demo.py`
- `examples/workflows/research-assistant.toml`
- `scripts/run_workflow.py`

The runtime is intentionally protocol-first, but now includes:

- tissue topology and local neighborhood routing
- real OpenAI-compatible remote provider adapters
- adaptive latent learning
- latent vector signaling, continuous regional diffusion, resonance, and similarity recall
- durable memory recall, trust curriculum, and immune hazard patterns
- regional circulation and homeostasis snapshots
- process-based distributed tissue execution
- SQLite-backed scheduling and execution persistence
- event persistence
- reserve-cell promotion
- recovery hooks
- config-driven workflow execution
