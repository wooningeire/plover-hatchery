from dataclasses import dataclass
from typing import Generic, TypeVar, final

from plover_hatchery.lib.trie.Transition import Transition


V = TypeVar("V")


@final
@dataclass
class LookupResult(Generic[V]):
    translation: V
    cost: float
    transitions: tuple[Transition, ...]
