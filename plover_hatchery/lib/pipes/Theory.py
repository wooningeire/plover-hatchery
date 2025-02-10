from dataclasses import dataclass
from collections.abc import Callable, Iterable
from typing import final

from ..trie import NondeterministicTrie
from ..sopheme import Sopheme


@final
@dataclass(frozen=True)
class Theory:
    add_entry: Callable[[NondeterministicTrie[str, int], Iterable[Sopheme], int], None]
    lookup: Callable[[NondeterministicTrie[str, int], tuple[str, ...], list[str]], "str | None"]
    reverse_lookup: Callable[[NondeterministicTrie[str, int], str, dict[str, list[int]]], list[tuple[str, ...]]]


