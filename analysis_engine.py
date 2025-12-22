import json
import csv
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import networkx as nx

# Reuse existing graph builder and helpers
try:
    from topic_graph import build_course_graph, detect_cycles
    # We might need to import more if logic is needed, but we re-implement specific checks here for control
except ImportError:
    # Fallback if running from a different context where sys.path isn't set, 
    # but strictly we should expect it to work if in root.
    pass

@dataclass
class Issue:
    code: str
    severity: str  # "high", "medium", "low"
    courses: List[str]
    message: str
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

@dataclass
class Report:
    source_path: str
    generated_at: str
    metrics: Dict[str, Any]
    issues: List[Issue]

    def to_dict(self):
        return {
            "source_path": self.source_path,
            "generated_at": self.generated_at,
            "metrics": self.metrics,
            "issues": [i.to_dict() for i in self.issues]
        }

def load_catalog(json_path: str) -> List[Dict[str, Any]]:
    """
    Loads and validates the raw catalog JSON.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if not isinstance(data, list):
        raise ValueError("Catalog must be a JSON list of course objects.")
        
    normalized = []
    for item in data:
        if "id" not in item:
            continue # Skip invalid items or raise? Using lax approach for now but could be stricter
        
        # Normalize prerequisites
        prereqs = item.get("prerequisites", [])
        if not isinstance(prereqs, list):
            prereqs = [] 
            
        filtered_item = {
            "id": item["id"],
            "name": item.get("name", "Unknown"),
            "prerequisites": prereqs
        }
        normalized.append(filtered_item)
        
    return normalized

def build_graph_from_catalog(json_path: str) -> nx.DiGraph:
    """
    Delegates to the existing topic_graph.build_course_graph to ensure consistency.
    """
    # We assume topic_graph is available. 
    # If we needed custom logic we would implement it here.
    return build_course_graph(json_path)

def check_cycles(graph: nx.DiGraph) -> List[Issue]:
    issues = []
    # Use existing detect_cycles which returns list of lists
    cycles = detect_cycles(graph)
    for cycle in cycles:
        issues.append(Issue(
            code="cycle",
            severity="high",
            courses=sorted(cycle),
            message=f"Cycle detected involving {len(cycle)} courses: {', '.join(cycle)}",
            meta={"cycle": cycle}
        ))
    return issues

def check_missing_prereqs(graph: nx.DiGraph, real_course_ids: Set[str]) -> List[Issue]:
    issues = []
    # In the graph, if we used build_course_graph, it adds nodes for prereqs even if they don't exist in the input.
    # So we check if any node in the graph is NOT in real_course_ids.
    
    # Alternatively, iterate real courses and check their prereqs manually.
    # The graph-based approach is cleaner if we trust the graph structure.
    # However, existing build_course_graph adds edge (prereq, course).
    # So if prereq X is missing, X is a node in graph.
    
    for node in graph.nodes():
        if node not in real_course_ids:
            # This is a missing ID (assuming build_course_graph added it precisely because it was a prereq)
            # Find who refers to it
            referenced_by = list(graph.successors(node)) # node -> successors means node is prereq for successors
            issues.append(Issue(
                code="missing_prereq",
                severity="high",
                courses=[node],
                message=f"Course '{node}' is required by {', '.join(referenced_by)} but not defined in catalog.",
                meta={"referenced_by": referenced_by}
            ))
    return issues

def check_isolated(graph: nx.DiGraph, real_course_ids: Set[str]) -> List[Issue]:
    issues = []
    for node in real_course_ids:
        if node in graph:
            in_deg = graph.in_degree(node)   # Prerequisites points TO this node? 
            # Wait, existing build_course_graph:
            # g.add_edge(prereq_id, course_id)
            # So prereq -> course.
            # in_degree = incoming edges = prerequisites.
            # out_degree = outgoing edges = courses that require this one.
            
            out_deg = graph.out_degree(node)
            
            if in_deg == 0 and out_deg == 0:
                issues.append(Issue(
                    code="isolated_course",
                    severity="low",
                    courses=[node],
                    message=f"Course '{node}' has no prerequisites and is not a prerequisite for any other course.",
                    meta={}
                ))
    return issues

def check_bottlenecks(graph: nx.DiGraph, real_course_ids: Set[str], top_k: int = 5, min_out_degree: int = 3) -> tuple[List[Issue], List[dict]]:
    # Bottleneck = high out_degree (prereq for many)
    candidates = []
    for node in real_course_ids:
        if node in graph:
            out_d = graph.out_degree(node)
            if out_d >= min_out_degree:
                candidates.append({"id": node, "out_degree": out_d})
    
    # Sort by degree desc
    candidates.sort(key=lambda x: x["out_degree"], reverse=True)
    
    top_bottlenecks = candidates[:top_k]
    issues = []
    for bot in top_bottlenecks:
        issues.append(Issue(
            code="bottleneck",
            severity="medium",
            courses=[bot["id"]],
            message=f"Course '{bot['id']}' is a prerequisite for {bot['out_degree']} courses.",
            meta={"out_degree": bot["out_degree"]}
        ))
    
    return issues, top_bottlenecks

def check_longest_chain(graph: nx.DiGraph) -> tuple[List[Issue], int, List[str], bool]:
    # Returns issues, length, path, blocked_by_cycles
    if not nx.is_directed_acyclic_graph(graph):
        return [], 0, [], True
    
    # Compute longest path in DAG
    try:
        longest_path = nx.dag_longest_path(graph)
        length = len(longest_path)
        
        issues = []
        if length > 6: # Configurable threshold, hardcoded for now or passed via config?
             issues.append(Issue(
                 code="long_chain",
                 severity="medium" if length > 8 else "low",
                 courses=[longest_path[-1]] if longest_path else [],
                 message=f"Long prerequisite chain of length {length} detected ending at {longest_path[-1]}.",
                 meta={"length": length, "path": longest_path}
             ))
        return issues, length, longest_path, False
    except Exception:
        # Fallback
        return [], 0, [], True

def analyze_catalog(json_path: str, config: Optional[Dict[str, Any]] = None) -> Report:
    if config is None:
        config = {}
        
    cat_data = load_catalog(json_path)
    real_ids = {c["id"] for c in cat_data}
    
    graph = build_graph_from_catalog(json_path)
    
    metrics = {
        "course_count": len(real_ids),
        "total_nodes_in_graph": len(graph.nodes),
    }
    
    all_issues = []
    
    # 1. Cycles
    cycle_issues = check_cycles(graph)
    all_issues.extend(cycle_issues)
    metrics["num_cycles"] = len(cycle_issues)
    
    # 2. Missing Prereqs
    missing_issues = check_missing_prereqs(graph, real_ids)
    all_issues.extend(missing_issues)
    metrics["num_missing_prereqs"] = len(missing_issues)
    
    # 3. Isolated
    iso_issues = check_isolated(graph, real_ids)
    all_issues.extend(iso_issues)
    metrics["num_isolated"] = len(iso_issues)
    
    # 4. Bottlenecks
    bot_issues, top_bots = check_bottlenecks(
        graph, 
        real_ids, 
        top_k=config.get("top_bottlenecks", 5),
        min_out_degree=config.get("min_bottleneck", 3)
    )
    all_issues.extend(bot_issues)
    metrics["top_bottlenecks"] = top_bots
    
    # 5. Longest Chain
    chain_issues, length, path, blocked = check_longest_chain(graph)
    all_issues.extend(chain_issues)
    metrics["longest_chain_len"] = length
    metrics["longest_chain_path"] = path
    metrics["longest_chain_blocked_by_cycles"] = blocked
    
    # Sort issues for stability
    # Severity order: high > medium > low
    sev_map = {"high": 0, "medium": 1, "low": 2}
    all_issues.sort(key=lambda x: (
        sev_map.get(x.severity, 99),
        x.code,
        x.courses[0] if x.courses else ""
    ))
    
    return Report(
        source_path=json_path,
        generated_at=datetime.now().isoformat(),
        metrics=metrics,
        issues=all_issues
    )

def write_report_json(report: Report, out_path: str):
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report.to_dict(), f, indent=2)

def write_issues_csv(report: Report, out_path: str):
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["severity", "code", "courses", "message"])
        for issue in report.issues:
            writer.writerow([
                issue.severity,
                issue.code,
                ",".join(issue.courses),
                issue.message
            ])
