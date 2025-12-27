# scripts/analyze.py

import argparse
import sys
import os
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import networkx as nx

# Ensure we can import from project root
# ( Moved to main() to avoid E402 )

# =========================================================
# 1. PURE ANALYSIS LAYER
# =========================================================


@dataclass
class GraphStats:
    node_count: int
    edge_count: int
    root_count: int
    longest_chain: Optional[int]


@dataclass
class CyclesResult:
    total_count: int
    shown_count: int
    cycles: List[List[str]]


@dataclass
class ChainResult:
    target: str
    chain: List[str]
    error: Optional[str]


def compute_stats(graph: nx.DiGraph) -> GraphStats:
    nodes = graph.number_of_nodes()
    edges = graph.number_of_edges()
    roots = sum(1 for n in graph.nodes() if graph.in_degree(n) == 0)

    longest = None
    if nx.is_directed_acyclic_graph(graph):
        try:
            longest = len(nx.dag_longest_path(graph))
        except Exception:
            pass  # Should not happen if check passed

    return GraphStats(nodes, edges, roots, longest)


def compute_cycles(graph: nx.DiGraph, max_cycles_limit: int = 5) -> CyclesResult:
    from topic_graph import detect_cycles

    raw_cycles = detect_cycles(graph)
    total = len(raw_cycles)

    normalized = []
    for c in raw_cycles:
        # Canonical form: rotate so smallest element is first
        if not c:
            normalized.append([])
            continue

        # Find index of min element
        min_idx = c.index(min(c))
        # Rotate
        canon = c[min_idx:] + c[:min_idx]
        normalized.append(canon)

    # Sort the list of cycles
    normalized.sort()

    shown = normalized[:max_cycles_limit]
    return CyclesResult(total, len(shown), shown)


def compute_chain(graph: nx.DiGraph, target_id: Optional[str] = None) -> ChainResult:
    if not target_id:
        # Deterministic default: first node with prerequisites
        candidates = [n for n in graph.nodes() if graph.in_degree(n) > 0]
        candidates.sort()
        if candidates:
            target_id = candidates[0]
        else:
            # Fallback for graph with no edges
            all_nodes = sorted(list(graph.nodes()))
            if all_nodes:
                target_id = all_nodes[0]
            else:
                return ChainResult("?", [], "Graph is empty")

    if target_id not in graph:
        return ChainResult(target_id, [], f"Course '{target_id}' not found")

    from logic import get_prereq_chain

    chain_data = get_prereq_chain(graph, target_id)
    # logic puts target at end
    chain_ids = [c["id"] for c in chain_data]
    return ChainResult(target_id, chain_ids, None)


def compute_unlocked(graph: nx.DiGraph, completed: List[str]) -> List[str]:
    # Returns sorted list of strings "Name (ID)"
    from logic import get_unlocked_topics

    unlocked_dicts = get_unlocked_topics(graph, set(completed))
    items = []
    for x in unlocked_dicts:
        name = x.get("name", "Unknown")
        cid = x["id"]
        items.append(f"{name} ({cid})")
    items.sort()
    return items


# =========================================================
# 2. FORMATTING LAYER
# =========================================================

# --- TEXT FORMATTERS ---


def format_stats_text(stats: GraphStats) -> str:
    lines = ["GRAPH STATS"]
    lines.append(f"Nodes: {stats.node_count}")
    lines.append(f"Edges: {stats.edge_count}")
    lines.append(f"Root courses: {stats.root_count}")
    lc = str(stats.longest_chain) if stats.longest_chain is not None else "N/A (Cycles)"
    lines.append(f"Longest chain: {lc}")
    return "\n".join(lines)


def format_cycles_text(res: CyclesResult) -> str:
    lines = ["CYCLES"]
    if res.total_count == 0:
        lines.append("No cycles detected")
    else:
        lines.append(
            f"Detected {res.total_count} cycle(s). showing first {res.shown_count}:"
        )
        for i, cyc in enumerate(res.cycles):
            lines.append(f"  {i + 1}. {' <-> '.join(cyc)}")
        if res.total_count > res.shown_count:
            lines.append(f"  ... and {res.total_count - res.shown_count} more")
    return "\n".join(lines)


def format_chain_text(res: ChainResult) -> str:
    lines = ["EXAMPLE PREREQUISITE CHAIN"]
    if res.error:
        lines.append(f"Could not resolve chain for '{res.target}': {res.error}")
    elif not res.chain:
        lines.append(f"Target: {res.target}")
        lines.append("No prerequisites found.")
    else:
        lines.append(f"Target: {res.target}")
        full_str = " -> ".join(res.chain)
        if len(full_str) > 80:
            lines.append(full_str[:77] + "...")
        else:
            lines.append(full_str)
    return "\n".join(lines)


def format_unlocked_text(items: List[str]) -> str:
    lines = ["UNLOCKED COURSES"]
    if not items:
        lines.append("No new courses unlocked (or all completed/blocked).")
    else:
        lines.append(f"Found {len(items)} unlocked:")
        for item in items:
            lines.append(f"  [+] {item}")
    return "\n".join(lines)


def format_report_text(
    source: str,
    stats: GraphStats,
    cycles: CyclesResult,
    chain: Optional[ChainResult],
    unlocked: Optional[List[str]],
) -> str:
    parts = []
    # Header
    parts.append("College Validator AI — Prerequisite Analysis Tool")
    parts.append(f"Source: {source}")
    parts.append("")

    parts.append(format_stats_text(stats))
    parts.append("")

    parts.append(format_cycles_text(cycles))
    parts.append("")

    if cycles.total_count > 0:
        parts.append("VALIDATION FAILURE: Cycles detected.")
        parts.append("Skipped Chain and Unlocked sections due to cycles.")
        return "\n".join(parts)

    if chain:
        parts.append(format_chain_text(chain))
        parts.append("")

    if unlocked is not None:
        parts.append(format_unlocked_text(unlocked))

    return "\n".join(parts)


# --- JSON FORMATTERS ---


def _base_json_wrapper(
    json_path: str, cmd: str, has_cycles: bool, skipped: List[str], data: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "schema_version": "1",
        "generated_by": "scripts/analyze.py",
        "input_json": str(json_path),
        "command": cmd,
        "validation": {
            "has_cycles": has_cycles,
            "status": "fail" if has_cycles else "pass",
        },
        "skipped_sections": skipped,
        "data": data,
    }


def format_stats_dict(stats: GraphStats) -> Dict[str, Any]:
    return asdict(stats)


def format_cycles_dict(res: CyclesResult) -> Dict[str, Any]:
    return {
        "total_cycles": res.total_count,
        "shown_cycles": res.shown_count,
        "cycles": res.cycles,
    }


def format_chain_dict(res: ChainResult) -> Dict[str, Any]:
    return {"target": res.target, "chain": res.chain, "error": res.error}


def format_unlocked_list(items: List[str]) -> List[str]:
    return items


# =========================================================
# 3. CLI LOGIC
# =========================================================


def _resolve_json_path(user_path: Optional[str]) -> str:
    if user_path:
        return user_path
    candidates = ["samples/sample-output.json", "snapshots/latest.json"]
    for c in candidates:
        if os.path.exists(c):
            return c
    print("Error: No JSON file found and none provided.", file=sys.stderr)
    sys.exit(2)


def _extract_json_arg(argv: List[str]) -> Tuple[Optional[str], List[str]]:
    new_argv = []
    json_val = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        val_found = None
        consumed = 1
        if arg == "--json":
            if i + 1 < len(argv):
                val_found = argv[i + 1]
                consumed = 2
            else:
                print("Error: --json requires an argument", file=sys.stderr)
                sys.exit(2)
        elif arg.startswith("--json="):
            val_found = arg.split("=", 1)[1]
            consumed = 1

        if val_found is not None:
            if json_val is not None and json_val != val_found:
                print(
                    "Error: Multiple different --json arguments provided.",
                    file=sys.stderr,
                )
                sys.exit(2)
            json_val = val_found
            i += consumed
        else:
            new_argv.append(arg)
            i += 1
    return json_val, new_argv


def _write_output(content: str, out_path: Optional[str]):
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
            # No print to stdout if out_path provided
    else:
        print(content)


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Ensure we can import from project root if running as script
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from topic_graph import build_course_graph

    # 1. HELP FIRST CHECK
    if "-h" in argv or "--help" in argv:
        parser = _build_parser()
        try:
            parser.parse_args(argv)
        except SystemExit as e:
            return e.code
        return 0

    # 2. PREPROCESS JSON
    json_path, clean_argv = _extract_json_arg(argv)

    # 3. PARSE REMAINING ARGS
    parser = _build_parser()
    args = parser.parse_args(clean_argv)

    # 4. RESOLVE JSON REAL PATH
    try:
        real_json_path = _resolve_json_path(json_path)
        if not os.path.exists(real_json_path):
            print(f"Error: File not found: {real_json_path}", file=sys.stderr)
            return 2
    except SystemExit as e:
        return e.code

    # 5. EXECUTE LOGIC
    try:
        graph = build_course_graph(real_json_path)
        cmd = args.command if args.command else "report"
        fmt_json = args.format == "json"
        out_path = args.out

        # Dispatch
        final_output = ""
        exit_code = 0

        if cmd == "report":
            stats = compute_stats(graph)
            # Safe access for defaults when running implicit 'report' command
            mc = getattr(args, "max_cycles", 5)
            cycles_res = compute_cycles(graph, mc)

            has_cycles = cycles_res.total_count > 0

            if has_cycles:
                exit_code = 2
                skipped = ["chain", "unlocked"]
                if fmt_json:
                    data = {
                        "stats": format_stats_dict(stats),
                        "cycles": format_cycles_dict(cycles_res),
                    }
                    wrapper = _base_json_wrapper(
                        real_json_path, cmd, True, skipped, data
                    )
                    final_output = json.dumps(wrapper, sort_keys=True, indent=2)
                else:
                    final_output = format_report_text(
                        real_json_path, stats, cycles_res, None, None
                    )
            else:
                # No cycles, compute rest
                c_target = getattr(args, "course", None)
                chain_res = compute_chain(graph, c_target)

                completed = getattr(args, "completed", [])
                if not completed:
                    # Deterministic default
                    cands = [n for n in graph.nodes() if graph.in_degree(n) == 0]
                    cands.sort()
                    if cands:
                        completed = [cands[0]]

                unlocked_res = compute_unlocked(graph, completed)

                if fmt_json:
                    data = {
                        "stats": format_stats_dict(stats),
                        "cycles": format_cycles_dict(cycles_res),
                        "chain": format_chain_dict(chain_res),
                        "unlocked": format_unlocked_list(unlocked_res),
                    }
                    wrapper = _base_json_wrapper(real_json_path, cmd, False, [], data)
                    final_output = json.dumps(wrapper, sort_keys=True, indent=2)
                else:
                    final_output = format_report_text(
                        real_json_path, stats, cycles_res, chain_res, unlocked_res
                    )

        elif cmd == "stats":
            stats = compute_stats(graph)
            if fmt_json:
                data = {"stats": format_stats_dict(stats)}
                wrapper = _base_json_wrapper(real_json_path, cmd, False, [], data)
                final_output = json.dumps(wrapper, sort_keys=True, indent=2)
            else:
                final_output = format_stats_text(stats)

        elif cmd == "cycles":
            cycles_res = compute_cycles(graph, args.max_cycles)
            if cycles_res.total_count > 0:
                exit_code = 2

            if fmt_json:
                data = {"cycles": format_cycles_dict(cycles_res)}
                wrapper = _base_json_wrapper(
                    real_json_path, cmd, cycles_res.total_count > 0, [], data
                )
                final_output = json.dumps(wrapper, sort_keys=True, indent=2)
            else:
                final_output = format_cycles_text(cycles_res)

        elif cmd == "chain":
            if not args.course:
                print(
                    "Error: --course is required for chain subcommand", file=sys.stderr
                )
                return 2
            chain_res = compute_chain(graph, args.course)
            if fmt_json:
                data = {"chain": format_chain_dict(chain_res)}
                wrapper = _base_json_wrapper(real_json_path, cmd, False, [], data)
                final_output = json.dumps(wrapper, sort_keys=True, indent=2)
            else:
                final_output = format_chain_text(chain_res)

        elif cmd == "unlocked":
            if not args.completed:
                print(
                    "Error: --completed is required for unlocked subcommand",
                    file=sys.stderr,
                )
                return 2
            unlocked_res = compute_unlocked(graph, args.completed)
            if fmt_json:
                data = {"unlocked": format_unlocked_list(unlocked_res)}
                wrapper = _base_json_wrapper(real_json_path, cmd, False, [], data)
                final_output = json.dumps(wrapper, sort_keys=True, indent=2)
            else:
                final_output = format_unlocked_text(unlocked_res)

        _write_output(final_output, out_path)
        return exit_code

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def _build_parser():
    parser = argparse.ArgumentParser(
        description="College Validator AI CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python main.py\n  python main.py stats --format json\n  python main.py --json data.json report",
    )
    # Global options for every command
    parser.add_argument("--json", help="Path to catalog JSON (can be placed anywhere)")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    parser.add_argument("--out", help="Write output to file instead of stdout")

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Mixin arguments for reuse
    def add_common_args(p):
        p.add_argument(
            "--format", choices=["text", "json"], default="text", help="Output format"
        )
        p.add_argument("--out", help="Write output to file")

    # REPORT
    p_report = subparsers.add_parser(
        "report", help="Show full analysis report (default)"
    )
    p_report.add_argument("--course", help="Target course for example chain")
    p_report.add_argument(
        "--completed", nargs="+", help="Completed course IDs for unlocked check"
    )
    p_report.add_argument(
        "--max-cycles", type=int, default=5, help="Max cycles to display"
    )
    add_common_args(p_report)

    # STATS
    p_stats = subparsers.add_parser("stats", help="Show graph statistics")
    add_common_args(p_stats)

    # CYCLES
    p_cycles = subparsers.add_parser("cycles", help="Show detected cycles")
    p_cycles.add_argument(
        "--max-cycles", type=int, default=5, help="Max cycles to display"
    )
    add_common_args(p_cycles)

    # CHAIN
    p_chain = subparsers.add_parser("chain", help="Show prerequisite chain")
    p_chain.add_argument("--course", required=True, help="Target course ID")
    add_common_args(p_chain)

    # UNLOCKED
    p_unlocked = subparsers.add_parser("unlocked", help="Show unlocked courses")
    p_unlocked.add_argument(
        "--completed", nargs="+", required=True, help="Completed course IDs"
    )
    add_common_args(p_unlocked)

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
