from dataclasses import dataclass, field
from typing import Protocol, TypeVar, final

from plover.steno import Stroke

from plover_hatchery.lib.trie.NondeterministicTrie import NondeterministicTrie
from plover_hatchery.lib.trie.TriePath import TriePath


K = TypeVar("K")
V = TypeVar("V")


@final
@dataclass(frozen=True)
class TrieTraversalContext:
    trie: NondeterministicTrie[str, int]
    current_outline: tuple[Stroke, ...] = ()
    current_path: TriePath = TriePath()
