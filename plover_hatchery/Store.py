from typing import final, Callable

from plover_hatchery.lib.trie.NondeterministicTrie import NondeterministicTrie

@final
class Store:
    def __init__(self):
        self.breakdown_translation: Callable[[str], str | None] | None = None
        self.breakdown_lookup: Callable[[tuple[str, ...], list[str]], str | None] | None = None
        self.trie: NondeterministicTrie | None = None
        self.translations: list[str] | None = None

store = Store()