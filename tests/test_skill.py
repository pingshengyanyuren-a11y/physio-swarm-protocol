from __future__ import annotations

from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "skills" / "physio-swarm-architect" / "SKILL.md"


class SkillTest(unittest.TestCase):
    def test_skill_exists(self) -> None:
        self.assertTrue(SKILL_PATH.exists())

    def test_skill_references_organs_and_runtime(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")
        for token in ("endocrine", "metabolic", "nervous", "immune", "physioswarm/runtime.py"):
            self.assertIn(token, content)


if __name__ == "__main__":
    unittest.main()
