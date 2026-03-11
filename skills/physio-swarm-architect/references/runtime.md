# Runtime Reference

Key modules:

- `physioswarm/types.py`
- `physioswarm/signal_bus.py`
- `physioswarm/cells.py`
- `physioswarm/registry.py`
- `physioswarm/organs.py`
- `physioswarm/config_runner.py`
- `physioswarm/runtime.py`
- `physioswarm/workflow.py`

Example:

- `examples/research_assistant_demo.py`
- `examples/workflows/research-assistant.toml`
- `scripts/run_workflow.py`

The runtime is intentionally protocol-first, but now includes:

- provider-style adapters
- event persistence
- reserve-cell promotion
- recovery hooks
- config-driven workflow execution
