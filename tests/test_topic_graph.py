import unittest
import json
import networkx as nx
import tempfile
import os
import sys

# Add parent directory to path to import topic_graph
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from topic_graph import build_course_graph, detect_cycles, get_unlocked_courses


class TestTopicGraph(unittest.TestCase):
    def setUp(self):
        self.test_data = [
            {"id": "CS101", "name": "Intro to CS", "prerequisites": []},
            {"id": "CS201", "name": "Data Structures", "prerequisites": ["CS101"]},
            {"id": "CS202", "name": "Discrete Math", "prerequisites": []},
            {"id": "CS301", "name": "Algorithms", "prerequisites": ["CS201", "CS202"]},
        ]

        # Create a temporary file
        self.temp_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding="utf-8"
        )
        json.dump(self.test_data, self.temp_file)
        self.temp_file.close()

    def tearDown(self):
        os.unlink(self.temp_file.name)

    def test_load_course_graph(self):
        g = build_course_graph(self.temp_file.name)
        self.assertIsInstance(g, nx.DiGraph)
        self.assertEqual(len(g.nodes), 4)
        self.assertEqual(len(g.edges), 3)  # CS101->CS201, CS201->CS301, CS202->CS301
        self.assertEqual(g.nodes["CS101"]["name"], "Intro to CS")

        # Check edges
        self.assertTrue(g.has_edge("CS101", "CS201"))
        self.assertTrue(g.has_edge("CS201", "CS301"))
        self.assertTrue(g.has_edge("CS202", "CS301"))

    def test_detect_cycles_no_cycle(self):
        g = build_course_graph(self.temp_file.name)
        cycles = detect_cycles(g)
        self.assertEqual(cycles, [])

    def test_detect_cycles_with_cycle(self):
        g = nx.DiGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "A")
        cycles = detect_cycles(g)
        self.assertTrue(len(cycles) > 0)

    def test_get_unlocked_courses(self):
        g = build_course_graph(self.temp_file.name)

        # No courses completed
        unlocked = get_unlocked_courses(g, [])
        self.assertCountEqual(unlocked, ["CS101", "CS202"])

        # CS101 completed
        unlocked = get_unlocked_courses(g, ["CS101"])
        self.assertCountEqual(unlocked, ["CS201", "CS202"])

        # CS101 and CS201 completed
        unlocked = get_unlocked_courses(g, ["CS101", "CS201"])
        self.assertCountEqual(unlocked, ["CS202"])  # CS301 needs CS202

        # CS101, CS201, CS202 completed
        unlocked = get_unlocked_courses(g, ["CS101", "CS201", "CS202"])
        self.assertCountEqual(unlocked, ["CS301"])

        # All completed
        unlocked = get_unlocked_courses(g, ["CS101", "CS201", "CS202", "CS301"])
        self.assertEqual(unlocked, [])


if __name__ == "__main__":
    unittest.main()
