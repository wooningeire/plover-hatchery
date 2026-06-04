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


def test__trie__traverses_single_keys_without_creating_unknown_keys() -> None:
    trie = Trie[tuple[str, int], object]()
    value = object()
    node = trie.follow(Trie.ROOT, ("key", 1))
    trie.set_translation(node, value)

    assert trie.traverse(Trie.ROOT, ("key", 1)) == node
    assert trie.traverse(Trie.ROOT, ("missing", 2)) is None
    assert trie.get_translation(node) is value
    assert not trie.node_has_translations(Trie.ROOT)


def test__readonly_trie__preserves_transitions_and_translations() -> None:
    trie = Trie[str, str]()
    node = trie.follow_chain(Trie.ROOT, ("K", "W", "R"))
    trie.set_translation(node, "query")

    readonly = trie.frozen()

    assert readonly.traverse_chain(readonly.ROOT, ("K", "W", "R")) == node
    assert readonly.traverse_chain(readonly.ROOT, ("K", "W", "S")) is None
    assert readonly.get_translation(node) == "query"
    assert readonly.node_has_translations(node)


def test__readonly_trie__freezes_transitions_but_tracks_translation_updates() -> None:
    trie = Trie[str, str]()
    existing_node = trie.follow_chain(Trie.ROOT, ("A",))
    readonly = trie.frozen()

    added_node = trie.follow_chain(Trie.ROOT, ("B",))
    trie.set_translation(existing_node, "updated")
    trie.set_translation(added_node, "added")

    assert readonly.traverse_chain(readonly.ROOT, ("A",)) == existing_node
    assert readonly.traverse_chain(readonly.ROOT, ("B",)) is None
    assert readonly.get_translation(existing_node) == "updated"
    assert readonly.node_has_translations(added_node)


def test__trie__stringifies_nodes_translations_and_transition_keys() -> None:
    trie = Trie[str, str]()
    node = trie.follow_chain(Trie.ROOT, ("S", "T"))
    trie.set_translation(node, "start")

    assert str(trie).splitlines() == [
        "0",
        "\tS\t ->\t 1",
        "1",
        "\tT\t ->\t 2",
        "2 : start",
    ]
