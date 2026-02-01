from dataclasses import dataclass
from collections.abc import Callable, Iterable
from typing import final, Protocol

from ..trie import NondeterministicTrie
from ..sopheme import Sopheme


@final
@dataclass(frozen=True)
class TheoryLookup:
    lookup: Callable[[tuple[str, ...]], str | None]
    reverse_lookup: Callable[[str], list[tuple[str, ...]]]
    breakdown_translation: Callable[[str], str | None]
    breakdown_lookup: Callable[[tuple[str, ...], list[str]], str | None]


@final
@dataclass(frozen=True)
class Theory:
    class BuildLookup(Protocol):
        def __call__(self, *, entry_lines: Iterable[tuple[str, str]], filename: str="") -> TheoryLookup: ...
        
    build_lookup: BuildLookup