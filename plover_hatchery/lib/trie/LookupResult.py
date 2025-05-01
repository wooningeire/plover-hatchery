from dataclasses import dataclass
from typing import Generic, TypeVar, final

from plover_hatchery.lib.trie.Transition import TransitionKey


V = TypeVar("V")


@final
@dataclass
class LookupResult(Generic[V]):
    translation: V
    translation_id: int
    cost: float
    transitions: tuple[TransitionKey, ...]
