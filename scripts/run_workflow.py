from __future__ import annotations

import argparse
from pathlib import Path

from physioswarm.config_runner import run_configured_workflow


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a configured physiological swarm workflow from a TOML file.")
    parser.add_argument("config", type=Path, help="Path to workflow TOML config.")
    args = parser.parse_args()

    result = run_configured_workflow(args.config)
    for artifact in result["artifacts"]:
        print(artifact)
    print("final_state", result["final_state"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
