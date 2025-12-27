from typing import List, Set, Dict, Any
import networkx as nx
from topic_graph import get_unlocked_courses


def get_prereq_chain(
    graph: nx.DiGraph, topic_id: str, visited: Set[str] | None = None
) -> List[Dict[str, Any]]:
    """
    Returns all prerequisites for topic_id (and the topic itself)
    in roughly topological order: prereqs first, then the topic.
    Returns list of node attribute dicts (including 'id').
    """
    if visited is None:
        visited = set()

    # prevent infinite loops if the graph has a cycle by mistake
    if topic_id in visited:
        return []

    visited.add(topic_id)

    if topic_id not in graph:
        return []

    # get attributes and inject id
    topic_attrs = graph.nodes[topic_id].copy()
    topic_attrs["id"] = topic_id

    chain: List[Dict[str, Any]] = []

    # 1) recursively gather all prerequisites
    # graph.predecessors(topic_id) gives direct parents
    # We want to iterate them in a consistent order if possible, though sets are unordered
    for pre_id in graph.predecessors(topic_id):
        chain.extend(get_prereq_chain(graph, pre_id, visited))

    # 2) then add this topic itself if not already in the chain
    # Note: dicts are not hashable so we can't use 'if topic in chain' easily if we rely on equality
    # But since we use ids for recursion, we can just check if we added it?
    # Actually, the recursion logic with 'visited' handles the graph traversal,
    # but 'chain' accumulation might dup if we have diamond dependencies.
    # The 'visited' set in the recursive call shares state?
    # No, 'visited' is passed down.
    # To strictly return a list without dups in topo order:

    # Actually, a simple topological sort of the subgraph ancestors is easier.
    # But sticking to the existing logic style:

    already_in_chain = {t["id"] for t in chain}
    if topic_id not in already_in_chain:
        chain.append(topic_attrs)

    return chain


def get_unlocked_topics(
    graph: nx.DiGraph, known_topic_ids: Set[str]
) -> List[Dict[str, Any]]:
    """
    Returns topics whose prerequisites are all satisfied by known_topic_ids,
    excluding topics the user already knows.
    Wraps topic_graph.get_unlocked_courses.
    """
    unlocked_ids = get_unlocked_courses(graph, known_topic_ids)

    results = []
    for uid in unlocked_ids:
        attrs = graph.nodes[uid].copy()
        attrs["id"] = uid
        results.append(attrs)

    return results
