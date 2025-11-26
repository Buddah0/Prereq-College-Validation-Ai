from typing import List, Set
from topic_graph import TopicGraph
from topic_model import Topic


def get_prereq_chain(
    graph: TopicGraph,
    topic_id: str,
    visited: Set[str] | None = None
) -> List[Topic]:
    """
    Returns all prerequisites for topic_id (and the topic itself)
    in roughly topological order: prereqs first, then the topic.

    This uses RECURSION over the graph.
    """
    if visited is None:
        visited = set()

    # prevent infinite loops if the graph has a cycle by mistake
    if topic_id in visited:
        return []

    visited.add(topic_id)

    topic = graph.get_topic(topic_id)
    chain: List[Topic] = []

    # 1) recursively gather all prerequisites
    for pre_id in topic.prerequisites:
        chain.extend(get_prereq_chain(graph, pre_id, visited))

    # 2) then add this topic itself if not already in the chain
    if topic not in chain:
        chain.append(topic)

    return chain


def get_unlocked_topics(graph: TopicGraph, known_topic_ids: Set[str]) -> List[Topic]:
    """
    Returns topics whose prerequisites are all satisfied by known_topic_ids,
    excluding topics the user already knows.
    """
    unlocked: List[Topic] = []

    for topic in graph.list_topics():
        if topic.id in known_topic_ids:
            continue

        if all(pre_id in known_topic_ids for pre_id in topic.prerequisites):
            unlocked.append(topic)

    return unlocked
