from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from physioswarm.distributed import ClusterRegistry


class ClusterRegistryTest(unittest.TestCase):
    def test_registry_tracks_nodes_and_prefers_healthy_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = ClusterRegistry(Path(temp_dir) / "cluster.sqlite3")
            try:
                registry.register("cortex", "http://node-a")
                registry.register("cortex", "http://node-b")
                registry.mark_health("http://node-a", healthy=False)
                registry.mark_health("http://node-b", healthy=True)

                endpoint = registry.resolve("cortex")

                self.assertEqual(endpoint, "http://node-b")
            finally:
                registry.close()
