from dataclasses import dataclass, field
from typing import List


@dataclass
class Topic:
    id: str                   # e.g. "arrays"
    name: str                 # e.g. "Arrays"
    description: str = ""     # short text; later we can feed this to the AI
    prerequisites: List[str] = field(default_factory=list)  # list of topic ids
