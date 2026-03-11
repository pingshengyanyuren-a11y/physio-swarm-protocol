from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from physioswarm.config_runner import load_plan_from_toml, run_configured_workflow


TOML_CONTENT = """
name = "research-assistant"

[[stages]]
name = "triage"
objective = "halt urgent recursion"
urgency = 0.92
noise = 0.10
complexity = 0.20

[[stages]]
name = "analysis"
objective = "synthesize evidence"
urgency = 0.55
noise = 0.30
complexity = 0.82

[[cells]]
organ = "reflex_arc"
cell_id = "reflex-1"

[[cells]]
organ = "cortex"
cell_id = "cortex-1"

[[reserve_cells]]
organ = "cortex"
cell_id = "reserve-cortex"
"""


class ConfigRunnerTest(unittest.TestCase):
    def test_load_plan_from_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "workflow.toml"
            config_path.write_text(TOML_CONTENT, encoding="utf-8")

            bundle = load_plan_from_toml(config_path)

            self.assertEqual(bundle.plan.name, "research-assistant")
            self.assertEqual(len(bundle.cells), 2)
            self.assertEqual(len(bundle.reserve_cells), 1)

    def test_run_configured_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "workflow.toml"
            config_path.write_text(TOML_CONTENT, encoding="utf-8")

            result = run_configured_workflow(config_path)

            self.assertEqual(result["plan"], "research-assistant")
            self.assertEqual(len(result["artifacts"]), 2)

    def test_workflow_script_runs_from_toml(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [
                sys.executable,
                str(repo_root / "scripts" / "run_workflow.py"),
                str(repo_root / "examples" / "workflows" / "research-assistant.toml"),
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("final_state", completed.stdout)


if __name__ == "__main__":
    unittest.main()
