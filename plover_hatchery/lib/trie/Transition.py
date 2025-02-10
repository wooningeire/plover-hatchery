from typing import NamedTuple, TypeVar, Generic
from dataclasses import dataclass


S = TypeVar("S")
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

class Transition(NamedTuple):
    node_index: int
    key_id: int
    transition_index: int

class TransitionCostKey(NamedTuple):
    transition: Transition
    value_id: int

@dataclass(frozen=True)
class TransitionCostInfo(Generic[V]):
    cost: float
    value: V
