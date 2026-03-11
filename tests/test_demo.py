from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from examples.research_assistant_demo import run_demo


class DemoTest(unittest.TestCase):
    def test_demo_returns_artifact_trail(self) -> None:
        result = run_demo()

        self.assertIn("artifacts", result)
        self.assertIn("signals", result)
        self.assertGreaterEqual(len(result["artifacts"]), 3)
        self.assertIn("final_state", result)

    def test_demo_script_runs(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, str(repo_root / "examples" / "research_assistant_demo.py")],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("final_state", completed.stdout)

    def test_package_module_entrypoint_runs(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "-m", "physioswarm"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("final_state", completed.stdout)


if __name__ == "__main__":
    unittest.main()
