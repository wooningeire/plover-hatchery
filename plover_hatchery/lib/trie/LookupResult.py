from dataclasses import dataclass
from typing import Generic, final

from plover_hatchery.lib.trie.Transition import TransitionKey

@final
@dataclass
class LookupResult:
    translation_id: int
    cost: float
    transitions: tuple[TransitionKey, ...]
