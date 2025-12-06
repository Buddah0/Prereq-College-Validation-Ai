import json
from pathlib import Path
from typing import Iterable, List, Dict, Set
import networkx as nx

def load_course_graph(json_path: str) -> nx.DiGraph:
    """
    Loads course data from a JSON file and builds a directed graph.
    
    Args:
        json_path: Path to the JSON file containing course data.
        
    Returns:
        A networkx.DiGraph where nodes are course IDs and edges represent prerequisites.
        Node attributes include 'name'.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    g = nx.DiGraph()
    
    for course in data:
        course_id = course["id"]
        # Add the node with attributes
        g.add_node(course_id, name=course["name"])
        
        # Add edges for prerequisites
        # If A is a prerequisite for B, the edges goes from A -> B
        # This means "A must be done before B"
        for prereq_id in course.get("prerequisites", []):
            g.add_edge(prereq_id, course_id)
            
    return g

def detect_cycles(graph: nx.DiGraph) -> List[List[str]]:
    """
    Detects simple cycles in the graph.
    
    Args:
        graph: The course graph.
        
    Returns:
        A list of cycles, where each cycle is a list of node IDs.
    """
    try:
        return list(nx.simple_cycles(graph))
    except (nx.NetworkXNoCycle, nx.NetworkXError):
        return []

def get_unlocked_courses(graph: nx.DiGraph, completed_courses: Iterable[str]) -> List[str]:
    """
    Identifies courses that are unlocked given a set of completed courses.
    
    A course is unlocked if:
    1. It is not already completed.
    2. All its direct prerequisites are in the completed_courses set.
    
    Args:
        graph: The course graph.
        completed_courses: A collection of course IDs that have been completed.
        
    Returns:
        A list of unlocked course IDs.
    """
    completed = set(completed_courses)
    unlocked = []
    
    for node in graph.nodes():
        if node in completed:
            continue
            
        # Check if all predecessors (prerequisites) are completed
        prerequisites = list(graph.predecessors(node))
        if all(prereq in completed for prereq in prerequisites):
            unlocked.append(node)
            
    return unlocked
