from topic_graph import build_course_graph, detect_cycles
from logic import get_prereq_chain, get_unlocked_topics
import os

def print_prereq_chain_example(graph):
    target_id = "CS201"
    chain = get_prereq_chain(graph, target_id)

    print(f"Prerequisite chain for '{target_id}':")
    for topic in chain:
        print(f"- {topic['name']} ({topic['id']})")


def print_unlocked_example(graph):
    known = {"MATH101", "ENGL100"}
    print("\nKnown topics:", known)

    unlocked = get_unlocked_topics(graph, known)

    print("\nBased on what you know, you can learn next:")
    for topic in unlocked:
        print(f"- {topic['name']} ({topic['id']})")

def run_analysis(json_path: str):
    print(f"Loading graph from {json_path}...")
    graph = build_course_graph(json_path)
    
    cycles = detect_cycles(graph)
    if cycles:
        print(f"WARNING: Cycles detected: {cycles}")
    else:
        print("No cycles detected.")
        
    print_prereq_chain_example(graph)
    print_unlocked_example(graph)

if __name__ == "__main__":
    # Use sample output by default
    sample_path = "samples/sample-output.json"
    if os.path.exists(sample_path):
        run_analysis(sample_path)
    else:
        print("Sample data not found.")
