import unittest
import json
import networkx as nx
import tempfile
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis_engine import (
    check_cycles,
    check_missing_prereqs,
    check_isolated,
    check_bottlenecks,
    check_longest_chain,
    Report,
    analyze_catalog,
)


class TestAnalysisEngine(unittest.TestCase):
    def setUp(self):
        # Temp file for catalog tests
        self.test_data = [
            {"id": "A", "name": "Course A", "prerequisites": []},
            {"id": "B", "name": "Course B", "prerequisites": ["A"]},
            {"id": "C", "name": "Course C", "prerequisites": ["B"]},
        ]
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding="utf-8"
        )
        json.dump(self.test_data, self.temp_file)
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_cycles_detection(self):
        g = nx.DiGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "A")

        issues = check_cycles(g)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "cycle")
        self.assertEqual(issues[0].severity, "high")
        self.assertIn("A", issues[0].courses)
        self.assertIn("B", issues[0].courses)

    def test_missing_prereqs(self):
        # Graph has A -> B, but only B is in real_ids
        g = nx.DiGraph()
        g.add_edge("A", "B")  # A is prereq for B

        real_ids = {"B"}
        issues = check_missing_prereqs(g, real_ids)

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "missing_prereq")
        self.assertEqual(issues[0].courses, ["A"])
        self.assertEqual(issues[0].severity, "high")

    def test_isolated_course(self):
        g = nx.DiGraph()
        g.add_node("A")
        real_ids = {"A"}

        issues = check_isolated(g, real_ids)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].code, "isolated_course")
        self.assertEqual(issues[0].courses, ["A"])

    def test_bottleneck(self):
        # A is needed by B, C, D, E
        g = nx.DiGraph()
        g.add_edge("A", "B")
        g.add_edge("A", "C")
        g.add_edge("A", "D")
        g.add_edge("A", "E")

        real_ids = {"A", "B", "C", "D", "E"}

        # Test with threshold 3
        issues, top = check_bottlenecks(g, real_ids, min_out_degree=3)
        self.assertTrue(len(issues) >= 1)
        self.assertEqual(issues[0].courses, ["A"])
        self.assertEqual(issues[0].severity, "medium")

    def test_long_chain(self):
        # A->B->C->D->E->F->G->H (length 7)
        g = nx.DiGraph()
        path = ["A", "B", "C", "D", "E", "F", "G", "H"]
        nx.add_path(g, path)

        issues, length, path_nodes, blocked = check_longest_chain(g)
        self.assertFalse(blocked)
        self.assertEqual(
            length, 8
        )  # path is [A, B, C, D, E, F, G, H] which has 8 nodes

        self.assertTrue(len(issues) > 0)
        self.assertEqual(issues[0].code, "long_chain")

    def test_analyze_catalog_integration(self):
        # Use temp file
        report = analyze_catalog(self.temp_file.name)
        self.assertIsInstance(report, Report)
        self.assertEqual(report.metrics["course_count"], 3)
        self.assertEqual(report.metrics["num_cycles"], 0)


if __name__ == "__main__":
    unittest.main()
