from typing import Dict, List
from topic_model import Topic


class TopicGraph:
    """
    Stores all topics and lets us look them up by id.
    """
    def __init__(self) -> None:
        # key: topic id, value: Topic object
        self.topics: Dict[str, Topic] = {}

    def add_topic(self, topic: Topic) -> None:
        self.topics[topic.id] = topic

    def get_topic(self, topic_id: str) -> Topic:
        return self.topics[topic_id]

    def list_topics(self) -> List[Topic]:
        return list(self.topics.values())


def build_sample_graph() -> TopicGraph:
    """
    Creates a small set of CS topics with prerequisites between them.
    """
    g = TopicGraph()

    g.add_topic(Topic(
        id="intro_programming",
        name="Intro Programming (variables, loops)",
        description="Basic variables, conditionals, and loops."
    ))

    g.add_topic(Topic(
        id="arrays",
        name="Arrays",
        description="Fixed-size sequences of elements.",
        prerequisites=["intro_programming"]
    ))

    g.add_topic(Topic(
        id="linked_lists",
        name="Linked Lists",
        description="Nodes linked by pointers/references.",
        prerequisites=["arrays"]
    ))

    g.add_topic(Topic(
        id="stacks",
        name="Stacks",
        description="LIFO data structure built on arrays/linked lists.",
        prerequisites=["arrays", "intro_programming"]
    ))

    g.add_topic(Topic(
        id="queues",
        name="Queues",
        description="FIFO data structure.",
        prerequisites=["arrays", "intro_programming"]
    ))

    g.add_topic(Topic(
        id="recursion",
        name="Recursion",
        description="Functions that call themselves.",
        prerequisites=["intro_programming"]
    ))

    g.add_topic(Topic(
        id="trees",
        name="Trees",
        description="Hierarchical data structure with parent/child nodes.",
        prerequisites=["linked_lists", "recursion"]
    ))

    g.add_topic(Topic(
        id="binary_search_trees",
        name="Binary Search Trees",
        description="Ordered tree structure for fast search.",
        prerequisites=["trees"]
    ))

    return g
