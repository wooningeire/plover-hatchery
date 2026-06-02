import pytest

from plover_hatchery.lib.trie import (
    NondeterministicTrie,
    TransitionCostInfo,
    TransitionCostKey,
    TransitionFlagManager,
    TransitionKey,
    TransitionSourceNode,
    TriePath,
)


def _transition_key_ids(transitions: list[TransitionKey]) -> tuple[int | None, ...]:
    return tuple(transition.key_id for transition in transitions)


def _result_key_ids(result) -> tuple[int | None, ...]:
    return _transition_key_ids(result.transitions)


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


def test__nondeterministic_trie__assigns_chain_cost_only_to_final_transition() -> None:
    trie = NondeterministicTrie()
    inserted_path = trie.follow_chain(
        NondeterministicTrie.ROOT,
        (1, 2, 3),
        TransitionCostInfo(3.5, 7),
    )
    trie.set_translation(inserted_path.dst_node_id, 7)

    results = trie.get_translations_and_costs((inserted_path,))

    assert _transition_key_ids(inserted_path.transitions) == (1, 2, 3)
    assert list(trie.get_transition_costs(inserted_path.transitions, 7)) == [0.0, 0.0, 3.5]
    assert [(result.translation_id, result.cost) for result in results] == [(7, 3.5)]
    with pytest.raises(KeyError):
        trie.get_transition_cost(inserted_path.transitions[0], 99)


def test__nondeterministic_trie__reuses_nodes_for_other_translations_but_forks_for_same_translation() -> None:
    trie = NondeterministicTrie()
    first_path = trie.follow_chain(
        NondeterministicTrie.ROOT,
        (1, 2),
        TransitionCostInfo(1.0, 7),
    )
    other_translation_path = trie.follow_chain(
        NondeterministicTrie.ROOT,
        (1, 2),
        TransitionCostInfo(2.0, 8),
    )
    repeated_translation_path = trie.follow_chain(
        NondeterministicTrie.ROOT,
        (1, 2),
        TransitionCostInfo(3.0, 7),
    )

    assert other_translation_path.dst_node_id == first_path.dst_node_id
    assert repeated_translation_path.dst_node_id != first_path.dst_node_id
    assert _transition_key_ids(repeated_translation_path.transitions) == (1, 2)


def test__nondeterministic_trie__follows_empty_transitions_after_key_but_not_as_explicit_key() -> None:
    trie = NondeterministicTrie()
    trie.follow(
        NondeterministicTrie.ROOT,
        None,
        TransitionCostInfo(0.5, 99),
    )
    keyed_path = trie.follow(
        NondeterministicTrie.ROOT,
        1,
        TransitionCostInfo(0.0, 7),
    )
    trie.follow(
        keyed_path.dst_node_id,
        None,
        TransitionCostInfo(1.5, 7),
    )

    keyed_paths = sorted(
        _transition_key_ids(path.transitions)
        for path in trie.traverse((TriePath.root(),), 1)
    )

    assert list(trie.traverse((TriePath.root(),), None)) == []
    assert keyed_paths == [(1,), (1, None)]


def test__nondeterministic_trie__link_join_chain_creates_cartesian_paths_to_common_destination() -> None:
    trie = NondeterministicTrie()
    left_path = trie.follow(
        NondeterministicTrie.ROOT,
        1,
        TransitionCostInfo(0.0, 7),
    )
    right_path = trie.follow(
        NondeterministicTrie.ROOT,
        2,
        TransitionCostInfo(0.0, 7),
    )

    joined_paths = trie.join_chain(
        (
            TransitionSourceNode(left_path.dst_node_id, 2.0),
            TransitionSourceNode(right_path.dst_node_id, 5.0),
        ),
        ((3,), (4,)),
        7,
    )
    trie.set_translation(joined_paths.dst_node_id, 7)

    traversed_paths = [
        path
        for key_ids in ((1, 3), (1, 4), (2, 3), (2, 4))
        for path in trie.traverse_chain((TriePath.root(),), key_ids)
    ]
    results = sorted(
        (_result_key_ids(result), result.cost)
        for result in trie.get_translations_and_costs(traversed_paths)
    )

    assert joined_paths.dst_node_id is not None
    assert len(joined_paths.transition_seqs) == 4
    assert results == [
        ((1, 3), 2.0),
        ((1, 4), 2.0),
        ((2, 3), 5.0),
        ((2, 4), 5.0),
    ]


def test__nondeterministic_trie__min_cost_lookup_keeps_lowest_cost_path_per_translation() -> None:
    trie = NondeterministicTrie()
    cheap_path = trie.follow_chain(
        NondeterministicTrie.ROOT,
        (1, 2),
        TransitionCostInfo(2.0, 7),
    )
    expensive_path = trie.follow_chain(
        NondeterministicTrie.ROOT,
        (3, 4),
        TransitionCostInfo(5.0, 7),
    )
    trie.set_translation(cheap_path.dst_node_id, 7)
    trie.set_translation(expensive_path.dst_node_id, 7)

    results = trie.get_translations_and_min_costs((cheap_path, expensive_path))

    assert [(result.translation_id, result.cost, _result_key_ids(result)) for result in results] == [
        (7, 2.0, (1, 2)),
    ]


def test__nondeterministic_trie__reverse_lookup_returns_costed_paths_for_translation() -> None:
    trie = NondeterministicTrie()
    first_path = trie.follow_chain(
        NondeterministicTrie.ROOT,
        (1, 2),
        TransitionCostInfo(2.0, 7),
    )
    second_path = trie.follow_chain(
        NondeterministicTrie.ROOT,
        (3, 4),
        TransitionCostInfo(5.0, 7),
    )
    trie.set_translation(first_path.dst_node_id, 7)
    trie.set_translation(second_path.dst_node_id, 7)

    reverse_lookup = trie.build_reverse_lookup()
    results = sorted(
        (_result_key_ids(result), result.cost)
        for result in reverse_lookup(7)
    )

    assert results == [
        ((1, 2), 2.0),
        ((3, 4), 5.0),
    ]


def test__nondeterministic_trie__subtrie_builder_adds_key_labels_costs_and_flags() -> None:
    trie = NondeterministicTrie()
    transition_flags = TransitionFlagManager()
    preferred_flag = transition_flags.new_flag("preferred")
    left_path = trie.follow(
        NondeterministicTrie.ROOT,
        1,
        TransitionCostInfo(0.0, 7),
    )
    right_path = trie.follow(
        NondeterministicTrie.ROOT,
        2,
        TransitionCostInfo(0.0, 7),
    )
    joined_paths = trie.join_chain(
        (
            TransitionSourceNode(left_path.dst_node_id, 2.0),
            TransitionSourceNode(right_path.dst_node_id, 5.0),
        ),
        ((3,), (4,)),
        7,
    )
    trie.set_translation(joined_paths.dst_node_id, 7)
    preferred_transition = joined_paths.transition_seqs[0].transitions[0]
    transition_flags.flag_transition(
        TransitionCostKey(preferred_transition, 7),
        preferred_flag,
    )

    build_subtrie = trie.build_subtrie_builder(
        transition_flags,
        lambda key_id: "(epsilon)" if key_id is None else f"k{key_id}",
    )
    subtrie = build_subtrie(7)

    assert subtrie is not None
    assert set(subtrie["nodes"]) == {
        NondeterministicTrie.ROOT,
        left_path.dst_node_id,
        right_path.dst_node_id,
        joined_paths.dst_node_id,
    }
    assert subtrie["translation_nodes"] == [joined_paths.dst_node_id]
    preferred_keys_costs = [
        keys_cost
        for transition in subtrie["transitions"]
        if (
            transition["src_node_id"] == preferred_transition.src_node_index
            and transition["dst_node_id"] == joined_paths.dst_node_id
        )
        for keys_cost in transition["keys_costs"]
        if keys_cost["key"] == f"k{preferred_transition.key_id}"
    ]
    assert preferred_keys_costs == [
        {
            "key": f"k{preferred_transition.key_id}",
            "cost": 2.0,
            "flags": ["preferred"],
        },
    ]


def test__nondeterministic_trie__traverse_handlers_can_filter_transitions() -> None:
    trie = NondeterministicTrie()
    trie.follow_chain(NondeterministicTrie.ROOT, (1, 2), TransitionCostInfo(1.0, 3))

    def block_second_key(_: NondeterministicTrie, __: TriePath, transition: TransitionKey) -> bool:
        return transition.key_id != 2

    trie.on_check_traverse(block_second_key)

    assert list(trie.traverse_chain((TriePath.root(),), (1, 2))) == []
