#!/usr/bin/env python3

from pathlib import Path
from typing import Iterable, List, Dict, Any, Set

import networkx as nx

# Adjust path to find modules if running as script from root or scripts dir
import sys
import os

# Add project root to sys.path so we can import from top-level modules
# This logic works if the script is in scripts/ and project root is one level up
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from topic_graph import build_course_graph, detect_cycles
from logic import get_prereq_chain, get_unlocked_topics

def print_prereq_chain_example(graph: nx.DiGraph, target_id: str = "CS201"):
    """
    Prints the prerequisite chain for a given target course.
    """
    chain = get_prereq_chain(graph, target_id)

    print(f"Prerequisite chain for '{target_id}':")
    if not chain:
        print("  (None or course not found)")
        return

    for topic in chain:
        # topic is a dict with 'id', 'name', etc.
        t_id = topic.get('id', '???')
        t_name = topic.get('name', 'Unknown')
        print(f"- {t_name} ({t_id})")


def print_unlocked_example(graph: nx.DiGraph, completed_courses: Iterable[str] = None):
    """
    Prints unlocked courses based on a set of completed courses.
    """
    if completed_courses is None:
        completed_courses = {"MATH101", "ENGL100"}
        
    known_set = set(completed_courses)
    print(f"\nKnown topics: {known_set}")

    unlocked = get_unlocked_topics(graph, known_set)

    print("\nBased on what you know, you can learn next:")
    if not unlocked:
        print("  (No new topics unlocked)")
        return
        
    for topic in unlocked:
        t_id = topic.get('id', '???')
        t_name = topic.get('name', 'Unknown')
        print(f"- {t_name} ({t_id})")


def analyze_course_graph(json_path: str):
    """
    Main analysis pipeline:
    1. Load graph
    2. Detect cycles
    3. Show examples
    """
    print(f"Loading graph from {json_path}...")
    try:
        graph = build_course_graph(json_path)
    except FileNotFoundError:
        print(f"Error: File not found at {json_path}")
        return
    except Exception as e:
        print(f"Error loading graph: {e}")
        return
    
    # 2. Detect cycles
    cycles = detect_cycles(graph)
    if cycles:
        print(f"WARNING: Cycles detected: {cycles}")
    else:
        print("No cycles detected.")
        
    # 3. Show examples
    print("-" * 40)
    print_prereq_chain_example(graph, "CS201")
    print("-" * 40)
    print_unlocked_example(graph, {"MATH101", "ENGL100"})
    print("-" * 40)

if __name__ == "__main__":
    # Default behavior if run directly
    sample_path = project_root / "samples" / "sample-output.json"
    analyze_course_graph(str(sample_path))
