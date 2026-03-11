from __future__ import annotations

import unittest

from physioswarm.registry import OrganRegistry
from physioswarm.cells import ReflexCell, ResearchCell


class RegistryTest(unittest.TestCase):
    def test_registry_builds_cells_from_specs(self) -> None:
        registry = OrganRegistry()
        registry.register("reflex_arc", lambda cell_id, reliability=0.95: ReflexCell(cell_id, reliability))
        registry.register("cortex", lambda cell_id, reliability=0.9: ResearchCell(cell_id, reliability))

        cells = registry.build_many(
            [
                {"organ": "reflex_arc", "cell_id": "reflex-1"},
                {"organ": "cortex", "cell_id": "cortex-1", "reliability": 0.72},
            ]
        )

        self.assertEqual(cells[0].state.organ, "reflex_arc")
        self.assertEqual(cells[1].state.cell_id, "cortex-1")
        self.assertAlmostEqual(cells[1].state.reliability, 0.72)


if __name__ == "__main__":
    unittest.main()
