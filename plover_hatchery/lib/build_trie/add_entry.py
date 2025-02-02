from typing import Optional

import plover.log

from ..trie import TransitionCostInfo, NondeterministicTrie
from ..config import TRIE_STROKE_BOUNDARY_KEY, TRIE_LINKER_KEY
from ..theory_defaults.amphitheory import amphitheory

from .state import EntryBuilderState, OutlineSounds
from .find_clusters import Cluster, handle_clusters
from .rules.left_consonants import add_left_consonant
from .rules.right_consonants import add_right_consonant

def add_entry(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
    state = EntryBuilderState(trie, sounds, translation)
    state.left_consonant_src_nodes = (trie.ROOT,)


    upcoming_clusters: dict[tuple[int, int], list[Cluster]] = {}

    for group_index, (consonants, vowel) in enumerate(sounds.nonfinals):
        state.group_index = group_index

        vowels_src_node: Optional[int] = None
        if len(consonants) == 0 and not state.is_first_consonant_set:
            vowels_src_node = trie.get_first_dst_node_else_create(state.left_consonant_src_nodes[0], TRIE_LINKER_KEY, TransitionCostInfo(0, translation))

        for phoneme_index, consonant in enumerate(consonants):
            state.phoneme_index = phoneme_index


            left_consonant_node, left_alt_consonant_node = add_left_consonant(state)


            right_consonant_node = state.right_consonant_src_nodes[0] if len(state.right_consonant_src_nodes) > 0 else None
            right_alt_consonant_node = state.last_right_alt_consonant_nodes[0] if len(state.last_right_alt_consonant_nodes) > 0 else None
            if not state.is_first_consonant_set:
                right_consonant_node, right_alt_consonant_node, rtl_stroke_boundary_adjacent_nodes = add_right_consonant(state, left_consonant_node)
                if rtl_stroke_boundary_adjacent_nodes is not None:
                    state.right_elision_squish_src_nodes = (rtl_stroke_boundary_adjacent_nodes[0],) if rtl_stroke_boundary_adjacent_nodes[0] is not None else ()
                    state.boundary_elision.set_nodes((rtl_stroke_boundary_adjacent_nodes[1],))

            handle_clusters(upcoming_clusters, left_consonant_node, right_consonant_node, state, False)

            state.left_consonant_src_nodes = state.prev_left_consonant_nodes = (left_consonant_node,)
            state.last_left_alt_consonant_nodes = (left_alt_consonant_node,) if left_alt_consonant_node is not None else ()
            state.right_consonant_src_nodes = (right_consonant_node,) if right_consonant_node is not None else ()
            state.last_right_alt_consonant_nodes = (right_alt_consonant_node,) if right_alt_consonant_node is not None else ()

        state.phoneme_index = len(consonants)

        state.left_squish_elision.set_src_nodes(state.left_consonant_src_nodes)
        # can't really do anything all that special with vowels, so only proceed through a vowel transition
        # if it matches verbatim
        if vowels_src_node is None:
            vowels_src_node = state.left_consonant_src_nodes[0]
        postvowels_node = trie.get_first_dst_node_else_create(vowels_src_node, amphitheory.spec.vowel_to_steno(vowel), TransitionCostInfo(0, translation))

        handle_clusters(upcoming_clusters, state.left_consonant_src_nodes[0], state.right_consonant_src_nodes[0] if len(state.right_consonant_src_nodes) > 0 else None, state, True)


        state.right_consonant_src_nodes = (postvowels_node,)
        state.left_consonant_src_nodes = (trie.get_first_dst_node_else_create(postvowels_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, translation)),)

        if amphitheory.spec.INITIAL_VOWEL_CHORD is not None and state.is_first_consonant_set and len(consonants) == 0:
            trie.link_chain(trie.ROOT, state.left_consonant_src_nodes[0], amphitheory.spec.INITIAL_VOWEL_CHORD.keys(), TransitionCostInfo(0, translation))

        state.prev_left_consonant_nodes = ()


    state.group_index = len(sounds.nonfinals)
    for phoneme_index, consonant in enumerate(sounds.final_consonants):
        state.phoneme_index = phoneme_index

        right_consonant_node, right_alt_consonant_node, _ = add_right_consonant(state, None)

        handle_clusters(upcoming_clusters, None, right_consonant_node, state, False)

        state.right_consonant_src_nodes = (right_consonant_node,) if right_consonant_node is not None else ()
        state.last_right_alt_consonant_nodes = (right_alt_consonant_node,) if right_alt_consonant_node is not None else ()

        state.left_consonant_src_nodes = ()

    if len(state.right_consonant_src_nodes) == 0:
        # The outline contains no vowels and is likely a brief
        return

    trie.set_translation(state.right_consonant_src_nodes[0], translation)
