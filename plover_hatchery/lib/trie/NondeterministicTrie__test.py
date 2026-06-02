from plover_hatchery.lib.trie import NondeterministicTrie, TransitionCostInfo, TransitionKey, TriePath


def test__nondeterministic_trie__returns_translation_costs_for_traversed_paths() -> None:
    trie = NondeterministicTrie()
    inserted_path = trie.follow_chain(
        NondeterministicTrie.ROOT,
        (1, 2),
        TransitionCostInfo(3.5, 7),
    )
    trie.set_translation(inserted_path.dst_node_id, 7)

    paths = list(trie.traverse_chain((TriePath.root(),), (1, 2)))
    results = trie.get_translations_and_costs(paths)

    assert len(paths) == 1
    assert paths[0].dst_node_id == inserted_path.dst_node_id
    assert [(result.translation_id, result.cost) for result in results] == [(7, 3.5)]


def test__nondeterministic_trie__traverse_handlers_can_filter_transitions() -> None:
    trie = NondeterministicTrie()
    trie.follow_chain(NondeterministicTrie.ROOT, (1, 2), TransitionCostInfo(1.0, 3))

    def block_second_key(_: NondeterministicTrie, __: TriePath, transition: TransitionKey) -> bool:
        return transition.key_id != 2

    trie.on_check_traverse(block_second_key)

    assert list(trie.traverse_chain((TriePath.root(),), (1, 2))) == []
