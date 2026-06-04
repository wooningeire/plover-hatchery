from typing import Generic, TypeVar, final

from plover_hatchery_lib_rs import ReadonlyTrie as RsReadonlyTrie, Trie as RsTrie


Key = TypeVar("Key")
Value = TypeVar("Value")


@final
class Trie(Generic[Key, Value]):
    ROOT = 0

    def __init__(self):
        self.__rs = RsTrie()

    def follow(self, src_node: int, key: Key):
        return self.__rs.follow(src_node, key)

    def follow_chain(self, src_node: int, keys: tuple[Key, ...]):
        return self.__rs.follow_chain(src_node, keys)

    def traverse(self, src_node: int, key: Key):
        return self.__rs.traverse(src_node, key)

    def traverse_chain(self, src_node: int, keys: tuple[Key, ...]):
        return self.__rs.traverse_chain(src_node, keys)

    def set_translation(self, node: int, translation: Value):
        self.__rs.set_translation(node, translation)

    def get_translation(self, node: int):
        return self.__rs.get_translation(node)

    def node_has_translations(self, node: int):
        return self.__rs.node_has_translations(node)

    def frozen(self):
        return ReadonlyTrie(self.__rs.frozen())

    def __str__(self):
        return str(self.__rs)


@final
class ReadonlyTrie(Generic[Key, Value]):
    ROOT = 0

    def __init__(self, rs: RsReadonlyTrie):
        self.__rs = rs

    def traverse(self, src_node: int, key: Key):
        return self.__rs.traverse(src_node, key)

    def traverse_chain(self, src_node: int, keys: tuple[Key, ...]):
        return self.__rs.traverse_chain(src_node, keys)

    def get_translation(self, node: int):
        return self.__rs.get_translation(node)

    def node_has_translations(self, node: int):
        return self.__rs.node_has_translations(node)
