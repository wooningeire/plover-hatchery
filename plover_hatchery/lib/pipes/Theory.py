from dataclasses import dataclass
from collections.abc import Callable, Iterable
from typing import final, Protocol

from ..trie import NondeterministicTrie
from ..sopheme import Sopheme


@final
@dataclass(frozen=True)
class Theory:
    class BuildLookup(Protocol):
        def __call__(self, *, entries: Iterable[str]) -> "tuple[Callable[[tuple[str, ...]], str | None], Callable[[str], list[tuple[str, ...]]]]": ...
    # class AddEntry(Protocol):
    #     def __call__(self, *, trie: NondeterministicTrie[str, int], sophemes: Iterable[Sopheme], entry_id: int) -> None: ...
    # class Lookup(Protocol):
    #     def __call__(self, *, trie: NondeterministicTrie[str, int], stroke_stenos: tuple[str, ...], translations: list[str]) -> "str | None": ...
    # class ReverseLookup(Protocol):
    #     def __call__(self, *, trie: NondeterministicTrie[str, int], translation: str, reverse_translations: dict[str, list[int]]) -> Iterable[tuple[str, ...]]: ...
    
    build_lookup: BuildLookup
    # add_entry: AddEntry
    # lookup: Lookup
    # reverse_lookup: ReverseLookup

