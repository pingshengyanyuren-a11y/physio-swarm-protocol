from __future__ import annotations

import unittest

from physioswarm.topology import TissueTopology


class TopologyTest(unittest.TestCase):
    def test_topology_limits_reachable_regions_by_hops(self) -> None:
        topology = TissueTopology()
        topology.connect("cortex", "hippocampus")
        topology.connect("hippocampus", "immune")
        topology.place("cortex-1", "cortex")
        topology.place("hippo-1", "hippocampus")
        topology.place("immune-1", "immune")

        nearby = topology.candidate_cells("cortex", hops=1)
        farther = topology.candidate_cells("cortex", hops=2)

        self.assertEqual(set(nearby), {"cortex-1", "hippo-1"})
        self.assertEqual(set(farther), {"cortex-1", "hippo-1", "immune-1"})
