from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from physioswarm.cli import run_demo


if __name__ == "__main__":
    result = run_demo()
    for artifact in result["artifacts"]:
        print(artifact)
    print("final_state", result["final_state"])
