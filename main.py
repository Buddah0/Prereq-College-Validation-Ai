from topic_graph import build_sample_graph
from logic import get_prereq_chain, get_unlocked_topics


def print_prereq_chain_example() -> None:
    graph = build_sample_graph()

    target_id = "binary_search_trees"
    chain = get_prereq_chain(graph, target_id)

    print(f"Prerequisite chain for '{target_id}':")
    for topic in chain:
        print(f"- {topic.name} ({topic.id})")


def print_unlocked_example() -> None:
    graph = build_sample_graph()

    known = {"intro_programming", "arrays"}
    print("\nKnown topics:", known)

    unlocked = get_unlocked_topics(graph, known)

    print("\nBased on what you know, you can learn next:")
    for topic in unlocked:
        print(f"- {topic.name} ({topic.id})")


if __name__ == "__main__":
    print_prereq_chain_example()
    print_unlocked_example()
