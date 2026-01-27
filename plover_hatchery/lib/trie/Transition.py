from typing import NamedTuple
from dataclasses import dataclass


class TransitionKey(NamedTuple):
    src_node_index: int
    key_id: int | None
    transition_index: int

class TransitionCostKey(NamedTuple):
    transition: TransitionKey
    translation_id: int

@dataclass(frozen=True)
class TransitionCostInfo:
    cost: float
    translation_id: int
