from typing import final

from .Trie import NondeterministicTrie


@final
class TrieIndex:
    def __init__(self):
        self.__tries: list[NondeterministicTrie[str, str]] = []

    def add(self, trie: NondeterministicTrie[str, str]):
        self.__tries.append(trie)

    def lookup(self, outline_steno: str):
        pass