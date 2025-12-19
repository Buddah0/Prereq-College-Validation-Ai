# scripts/analyze.py

import argparse
import sys
import os
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import networkx as nx

# Ensure we can import from project root
# (In case this script is run directly)
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from topic_graph import build_course_graph, detect_cycles
from logic import get_prereq_chain, get_unlocked_topics

@dataclass
class Report:
    source_path: str
    nodes_count: int
    edges_count: int
    roots_count: int
    longest_chain_length: Optional[int]
    cycles: List[List[str]]
    example_chain: Optional[Dict[str, Any]]  # {"target": str, "chain": [str names/ids]}
    unlocked_courses: List[str] # List of strings "Name (ID)"
    error: Optional[str] = None

def build_report(
    json_path: str,
    completed: List[str],
    chain_target: Optional[str],
    max_cycles: int
) -> Report:
    
    # Defaults
    nodes = 0
    edges = 0
    roots = 0
    longest_len = None
    all_cycles = []
    ex_chain = None
    unlocked = []
    
    try:
        if not os.path.exists(json_path):
             return Report(json_path, 0, 0, 0, None, [], None, [], error=f"File not found: {json_path}")

        graph = build_course_graph(json_path)
        
        nodes = graph.number_of_nodes()
        edges = graph.number_of_edges()
        
        # Roots (in-degree 0)
        roots = sum(1 for n in graph.nodes() if graph.in_degree(n) == 0)
        
        # Cycles
        raw_cycles = detect_cycles(graph)
        # Sort cycles deterministically: 
        # 1. Sort nodes within each cycle
        # 2. Sort the list of cycles by the first node (and subsequent nodes)
        normalized_cycles = []
        for c in raw_cycles:
            # We want a stable representation. 
            # E.g. [B, A] -> [A, B]. 
            # Note: A cycle is a ring, so rotation matters but set doesn't.
            # But detect_cycles usually returns them in some order.
            # We'll just sort the list for display "set" purposes unless topology matters.
            # Creating a deterministic "canonical" form: rotate so smallest element is first?
            # User requirement: "stable ordering across runs".
            # Simple sort of elements is stable for display if we treat it as "Cycle involving {A, B}".
            normalized_cycles.append(sorted(c))
            
        normalized_cycles.sort()
        all_cycles = normalized_cycles
        
        # Longest chain
        # Only if no cycles, or we try-catch
        if not all_cycles:
            try:
                longest_len = len(nx.dag_longest_path(graph))
            except:
                pass
        
        # Example Chain
        target_id = chain_target
        if not target_id:
            # Pick deterministic default: "lexicographically first... course that has prerequisites"
            candidates = [n for n in graph.nodes() if graph.in_degree(n) > 0]
            candidates.sort() # Lexicographical sort
            if candidates:
                target_id = candidates[0]
        
        if target_id and target_id in graph:
            # Use logic.get_prereq_chain
            chain_data = get_prereq_chain(graph, target_id)
            # chain_data is list of dicts. We want a visual list of IDs.
            # get_prereq_chain includes the target at the end usually.
            chain_ids = [item['id'] for item in chain_data]
            ex_chain = {"target": target_id, "chain": chain_ids}
        elif target_id:
             # User asked for specific target but not found
             ex_chain = {"target": target_id, "chain": [], "error": "Course not found"}

        # Unlocked
        # logic.get_unlocked_topics returns list of dicts
        unlocked_dicts = get_unlocked_topics(graph, set(completed))
        # Format: "Name (ID)" and sort
        unlocked_items = []
        for x in unlocked_dicts:
            unlocked_items.append(f"{x.get('name', 'Unknown')} ({x['id']})")
        unlocked_items.sort()
        unlocked = unlocked_items

    except Exception as e:
        return Report(json_path, 0, 0, 0, None, [], None, [], error=str(e))

    return Report(
        source_path=json_path,
        nodes_count=nodes,
        edges_count=edges,
        roots_count=roots,
        longest_chain_length=longest_len,
        cycles=all_cycles,
        example_chain=ex_chain,
        unlocked_courses=unlocked
    )

def format_report(report: Report, max_cycles: int = 5) -> str:
    lines = []
    
    # A) Header
    lines.append("College Validator AI — Prerequisite Analysis Tool")
    lines.append(f"Source: {report.source_path}")
    lines.append("") # Hint could go here if needed, keeping clean
    
    if report.error:
        lines.append(f"CRITICAL ERROR: {report.error}")
        return "\n".join(lines)

    # B) Graph Stats
    lines.append("GRAPH STATS")
    lines.append(f"Nodes: {report.nodes_count}")
    lines.append(f"Edges: {report.edges_count}")
    lines.append(f"Root courses: {report.roots_count}")
    lc_str = str(report.longest_chain_length) if report.longest_chain_length is not None else "N/A (Cycles)"
    lines.append(f"Longest chain: {lc_str}")
    lines.append("")

    # C) Cycles
    lines.append("CYCLES")
    if report.cycles:
        count = len(report.cycles)
        lines.append(f"Detected {count} cycle(s). showing first {min(count, max_cycles)}:")
        for i, cyc in enumerate(report.cycles[:max_cycles]):
            # cyc is a sorted list of ids
            lines.append(f"  {i+1}. {' <-> '.join(cyc)}")
        if count > max_cycles:
            lines.append(f"  ... and {count - max_cycles} more")
    else:
        lines.append("No cycles detected")
    lines.append("")

    # D) Example Chain
    lines.append("EXAMPLE PREREQUISITE CHAIN")
    if report.example_chain:
        tgt = report.example_chain["target"]
        chain = report.example_chain.get("chain", [])
        err = report.example_chain.get("error")
        
        if err:
             lines.append(f"Could not resolve chain for '{tgt}': {err}")
        elif chain:
            # Format: A -> B -> C
            lines.append(f"Target: {tgt}")
            # Truncate if extremely long? prompt says "truncate nicely".
            # Let's arbitrary truncate at 10 items for readability if needed, or just print wrapper
            # Standard arrow
            arrow_chain = " -> ".join(chain)
            if len(arrow_chain) > 100:
                # Simple truncation logic
                 lines.append(arrow_chain[:97] + "...")
            else:
                 lines.append(arrow_chain)
        else:
            lines.append(f"No prerequisites found for {tgt}")
    else:
        lines.append("No prerequisites info available.")
    lines.append("")

    # E) Unlocked Courses
    lines.append("UNLOCKED COURSES")
    if report.unlocked_courses:
        lines.append(f"Found {len(report.unlocked_courses)} unlocked:")
        for item in report.unlocked_courses:
            lines.append(f"  [+] {item}")
    else:
        lines.append("No new courses unlocked (or all completed/blocked).")
    
    return "\n".join(lines)

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="College Validator AI CLI")
    parser.add_argument("--json", help="Path to catalog JSON")
    parser.add_argument("--completed", nargs="+", help="Space-separated list of completed course IDs")
    parser.add_argument("--chain", help="Specific course ID to show chain for")
    parser.add_argument("--max-cycles", type=int, default=5, help="Max cycles to display")
    
    args = parser.parse_args(argv)
    
    # Resolve JSON path
    json_path = args.json
    if not json_path:
        # Default resolution order
        candidates = [
            "samples/sample-output.json",
            "snapshots/latest.json"
        ]
        for c in candidates:
            if os.path.exists(c):
                json_path = c
                break
    
    if not json_path:
        print("Error: No JSON file found. Please provide --json or ensure 'samples/sample-output.json' exists.")
        return 2

    completed = args.completed if args.completed else []
    
    try:
        data = build_report(
            json_path=json_path,
            completed=completed,
            chain_target=args.chain,
            max_cycles=args.max_cycles
        )
        
        out = format_report(data, args.max_cycles)
        print(out)
        
        if data.error:
            return 1
            
        return 0
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())

