from typing import NamedTuple, TypeVar, Generic
from dataclasses import dataclass


S = TypeVar("S")
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

class TransitionKey(NamedTuple):
    src_node_index: int
    key_id: "int | None"
    transition_index: int

class TransitionCostKey(NamedTuple):
    transition: TransitionKey
    translation_id: int

@dataclass(frozen=True)
class TransitionCostInfo(Generic[V]):
    cost: float
    translation: V
