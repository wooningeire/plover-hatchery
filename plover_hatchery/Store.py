from typing import final, Callable

from plover_hatchery.lib.pipes.types import Soph
from plover_hatchery.lib.trie.NondeterministicTrie import NondeterministicTrie

@final
class Store:
    def __init__(self):
        self.reverse_lookup: Callable[[str], list[tuple[str, ...]]] | None = None
        self.trie: NondeterministicTrie[Soph] | None = None
        self.translations: list[str] | None = None

store = Store()