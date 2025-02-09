from dataclasses import dataclass
from collections.abc import Callable, Iterable
from typing import final

from plover_hatchery.lib.trie import TrieIndex

from ..trie import NondeterministicTrie
from ..sopheme import Sopheme


@final
@dataclass(frozen=True)
class Theory:
    add_entry: Callable[[TrieIndex, Iterable[Sopheme], str], None]
    lookup: Callable[[TrieIndex, tuple[str, ...]], "str | None"]
    reverse_lookup: Callable[[TrieIndex, str], list[tuple[str, ...]]]


