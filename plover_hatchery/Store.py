from typing import final, Callable

@final
class Store:
    def __init__(self):
        self.reverse_lookup: Callable[[str], list[tuple[str, ...]]] | None = None
        self.trie: NondeterministicTrie[Soph, EntryIndex] | None = None
        self.translations: list[str] | None = None

store = Store()