from typing import final

from .Trie import NondeterministicTrie


@final
class TrieIndex:
    def __init__(self):
        self.__tries: list[NondeterministicTrie[str, int]] = []

    def add(self, trie: NondeterministicTrie[str, int]):
        self.__tries.append(trie)

    def lookup(self, outline_steno: str):
        pass