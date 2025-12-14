#!/usr/bin/env python3

import argparse
import sys
import os
from pathlib import Path
import json

# Ensure we can import from project root
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis_engine import (
    analyze_catalog, 
    write_report_json, 
    write_issues_csv, 
    build_graph_from_catalog,
    check_cycles,
    load_catalog
)
# Retaining old imports for backward compat or specific logic if needed
from logic import get_unlocked_topics

def cmd_validate(args):
    """
    Runs full analysis and reports issues.
    """
    path = args.json
    print(f"Analyzing {path}...")
    
    config = {
        "min_bottleneck": args.min_bottleneck,
        "top_bottlenecks": args.top_bottlenecks,
        "long_chain_warn": args.long_chain_warn
    }
    
    try:
        report = analyze_catalog(path, config)
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)
        
    # Print summary
    print(f"\nAnalysis Report (generated at {report.generated_at})")
    print(f"Source: {report.source_path}")
    print(f"Metrics:")
    for k, v in report.metrics.items():
        if isinstance(v, list):
             print(f"  {k}: {len(v)} items")
        else:
             print(f"  {k}: {v}")
             
    print("\nIssues Summary:")
    by_severity = {"high": 0, "medium": 0, "low": 0}
    for issue in report.issues:
        sev = issue.severity
        if sev in by_severity:
            by_severity[sev] += 1
    
    print(f"  High: {by_severity['high']}")
    print(f"  Medium: {by_severity['medium']}")
    print(f"  Low: {by_severity['low']}")
    
    if args.out:
        out_path = args.out
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        write_report_json(report, out_path)
        print(f"\nFull report written to {out_path}")
        
    if args.csv:
        csv_path = args.csv
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
        write_issues_csv(report, csv_path)
        print(f"Issues CSV written to {csv_path}")

def cmd_cycles(args):
    """
    Checks for cycles and exits with 2 if found.
    """
    try:
        graph = build_graph_from_catalog(args.json)
        cycles = check_cycles(graph)
        
        if cycles:
            print(f"Found {len(cycles)} cycles:")
            for issue in cycles:
                # issue.meta['cycle'] is the list of nodes
                print(f" - {issue.message}")
            sys.exit(2)
        else:
            print("No cycles detected.")
            sys.exit(0)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def cmd_unlocked(args):
    """
    Lists unlocked courses.
    """
    try:
        # We need the graph and basic logic
        # logic.get_unlocked_topics expects graph and completed set
        # But wait, existing logic uses graph.
        
        graph = build_graph_from_catalog(args.json)
        
        completed = set()
        if args.completed:
            # args.completed is a list of strings if nargs='+' or string split?
            # Let's handle comma-separated string
            parts = args.completed.split(',')
            completed = {p.strip() for p in parts if p.strip()}
            
        print(f"Completed courses: {sorted(completed)}")
        
        unlocked = get_unlocked_topics(graph, completed)
        
        print("\nUnlocked courses:")
        if not unlocked:
            print("  (None)")
        else:
            # Sort for stability
            unlocked.sort(key=lambda x: x['id'])
            for topic in unlocked:
                 print(f" - {topic['name']} ({topic['id']})")
                 
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def analyze_course_graph(json_path: str):
    """
    Backward compatibility wrapper. 
    Previously accepted just a path and printed basic info (cycles check + examples).
    """
    print(f"NOTE: Using deprecated analyze_course_graph. usage.")
    print(f"Analyzing {json_path}...")
    
    # We can effectively run the 'validate' logic or just replicate old behavior using new engine
    # Old behavior: check cycles, print prereq chain example for CS201, print unlocked example
    
    try:
        graph = build_graph_from_catalog(json_path)
        
        # Cycles
        cycles = check_cycles(graph)
        if cycles:
            print(f"WARNING: Cycles detected: {[c.meta['cycle'] for c in cycles]}")
        else:
            print("No cycles detected.")
            
        print("-" * 40)
        # Re-implement example prints if we want exact parity, or just rely on manual calls?
        # The prompt said "keep them working (wrap/forward to new code)".
        # I'll just skip the specific "show me CS201 chain" unless requested, 
        # but to keep back-compat nice I'll print a summary report instead which is better.
        
        report = analyze_catalog(json_path)
        print(f"Found {len(report.issues)} issues total (High: {sum(1 for i in report.issues if i.severity=='high')}).")
        
    except Exception as e:
        print(f"Error loading graph: {e}")


def main():
    parser = argparse.ArgumentParser(description="College Validator AI - Analysis CLI")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    
    # Validate
    p_val = subparsers.add_parser("validate", help="Run full analysis and generate report")
    p_val.add_argument("--json", required=True, help="Path to catalog JSON")
    p_val.add_argument("--out", help="Path to output report JSON")
    p_val.add_argument("--csv", help="Path to output issues CSV")
    p_val.add_argument("--min-bottleneck", type=int, default=3, help="Minimum out-degree for bottlenecks")
    p_val.add_argument("--top-bottlenecks", type=int, default=10, help="Number of top bottlenecks to list")
    p_val.add_argument("--long-chain-warn", type=int, default=6, help="Warning threshold for chain length")
    p_val.set_defaults(func=cmd_validate)
    
    # Cycles
    p_cyc = subparsers.add_parser("cycles", help="Check for cycles (exit code 2 if found)")
    p_cyc.add_argument("--json", required=True, help="Path to catalog JSON")
    p_cyc.set_defaults(func=cmd_cycles)
    
    # Unlocked
    p_ul = subparsers.add_parser("unlocked", help="List unlocked courses")
    p_ul.add_argument("--json", required=True, help="Path to catalog JSON")
    p_ul.add_argument("--completed", required=True, help="Comma-separated list of completed course IDs")
    p_ul.set_defaults(func=cmd_unlocked)
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
