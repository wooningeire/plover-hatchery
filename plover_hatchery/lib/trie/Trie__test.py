from plover_hatchery.lib.trie.Trie import Trie


def test__trie__follows_and_traverses_key_chains() -> None:
    trie = Trie[str, str]()
    node = trie.follow_chain(Trie.ROOT, ("S", "T"))
    trie.set_translation(node, "start")

    assert trie.follow_chain(Trie.ROOT, ("S", "T")) == node
    assert trie.traverse_chain(Trie.ROOT, ("S", "T")) == node
    assert trie.traverse_chain(Trie.ROOT, ("S", "K")) is None
    assert trie.get_translation(node) == "start"
    assert trie.node_has_translations(node)


def test__readonly_trie__preserves_transitions_and_translations() -> None:
    trie = Trie[str, str]()
    node = trie.follow_chain(Trie.ROOT, ("K", "W", "R"))
    trie.set_translation(node, "query")

    readonly = trie.frozen()

    assert readonly.traverse_chain(readonly.ROOT, ("K", "W", "R")) == node
    assert readonly.traverse_chain(readonly.ROOT, ("K", "W", "S")) is None
    assert readonly.get_translation(node) == "query"
    assert readonly.node_has_translations(node)
