from dataclasses import dataclass
from collections.abc import Callable
from typing import final

from ..trie import NondeterministicTrie
from .state import OutlineSounds


@final
@dataclass(frozen=True)
class Theory:
    add_entry: Callable[[NondeterministicTrie[str, str], OutlineSounds, str], None]
    lookup: Callable[[NondeterministicTrie[str, str], tuple[str, ...]], "str | None"]
    reverse_lookup: Callable[[NondeterministicTrie[str, str], str], list[tuple[str, ...]]]


