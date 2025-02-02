from ..trie import NondeterministicTrie, TransitionCostInfo
from ..config import TRIE_STROKE_BOUNDARY_KEY, TRIE_LINKER_KEY
from ..theory_defaults.amphitheory import amphitheory
from .SoundsEnumerator import SoundsEnumerator
from .state import EntryBuilderState, OutlineSounds, ConsonantVowelGroup
from .find_clusters import Cluster, handle_clusters
from .rules.left_consonants import add_left_consonant
from .rules.right_consonants import add_right_consonant
from .Hook import Hook

class ManageStateHooks:
    def __init__(self):
        self.complete_nonfinal_group: Hook[EntryBuilderState, ConsonantVowelGroup] = Hook()

def use_manage_state(enumerator: SoundsEnumerator):
    hooks = ManageStateHooks()


    state: EntryBuilderState 

    vowels_src_node: "int | None"

    upcoming_clusters: dict[tuple[int, int], list[Cluster]]


    @enumerator.begin.listen
    def _(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        nonlocal state
        nonlocal upcoming_clusters

        state = EntryBuilderState(trie, sounds, translation)
        state.left_consonant_src_nodes = (trie.ROOT,)

        upcoming_clusters = {}


    @enumerator.begin_nonfinal_group.listen
    def _(group_index: int, group: ConsonantVowelGroup):
        nonlocal vowels_src_node

        state.group_index = group_index

        vowels_src_node = None
        if len(group.consonants) == 0 and not state.is_first_consonant_set:
            vowels_src_node = state.trie.get_first_dst_node_else_create(
                state.left_consonant_src_nodes[0],
                TRIE_LINKER_KEY,
                TransitionCostInfo(0, state.translation)
            )


    @enumerator.nonfinal_consonant.listen
    def _(consonant_index: int):
        state.phoneme_index = consonant_index


        left_consonant_node, left_alt_consonant_node = add_left_consonant(state)


        right_consonant_node = state.right_consonant_src_nodes[0] if len(state.right_consonant_src_nodes) > 0 else None
        right_alt_consonant_node = state.last_right_alt_consonant_nodes[0] if len(state.last_right_alt_consonant_nodes) > 0 else None
        if not state.is_first_consonant_set:
            right_consonant_node, right_alt_consonant_node, rtl_stroke_boundary_adjacent_nodes = add_right_consonant(state, left_consonant_node)
            if rtl_stroke_boundary_adjacent_nodes is not None:
                state.right_squish_elision.set_src_nodes((rtl_stroke_boundary_adjacent_nodes[0],) if rtl_stroke_boundary_adjacent_nodes[0] is not None else ())
                state.boundary_elision.set_src_nodes((rtl_stroke_boundary_adjacent_nodes[1],))

        handle_clusters(upcoming_clusters, left_consonant_node, right_consonant_node, state, False)


        state.left_consonant_src_nodes = state.prev_left_consonant_nodes = (left_consonant_node,)
        state.last_left_alt_consonant_nodes = (left_alt_consonant_node,) if left_alt_consonant_node is not None else ()
        state.right_consonant_src_nodes = (right_consonant_node,) if right_consonant_node is not None else ()
        state.last_right_alt_consonant_nodes = (right_alt_consonant_node,) if right_alt_consonant_node is not None else ()

    
    @enumerator.complete_nonfinal_group.listen
    def _(group: ConsonantVowelGroup):
        nonlocal vowels_src_node

        state.phoneme_index = len(group.consonants)

        state.left_squish_elision.set_src_nodes(state.left_consonant_src_nodes)
        # can't really do anything all that special with vowels, so only proceed through a vowel transition
        # if it matches verbatim
        if vowels_src_node is None:
            vowels_src_node = state.left_consonant_src_nodes[0]
        postvowels_node = state.trie.get_first_dst_node_else_create(vowels_src_node, amphitheory.spec.vowel_to_steno(group.vowel), TransitionCostInfo(0, state.translation))

        handle_clusters(upcoming_clusters, state.left_consonant_src_nodes[0], state.right_consonant_src_nodes[0] if len(state.right_consonant_src_nodes) > 0 else None, state, True)


        state.right_consonant_src_nodes = (postvowels_node,)
        state.left_consonant_src_nodes = (state.trie.get_first_dst_node_else_create(postvowels_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.translation)),)

        state.prev_left_consonant_nodes = ()


        hooks.complete_nonfinal_group.emit(state, group)

    
    @enumerator.begin_final_group.listen
    def _(group_index: int):
        state.group_index = group_index

    
    @enumerator.final_consonant.listen
    def _(consonant_index: int):
        state.phoneme_index = consonant_index


        right_consonant_node, right_alt_consonant_node, _ = add_right_consonant(state, None)

        handle_clusters(upcoming_clusters, None, right_consonant_node, state, False)

        state.right_consonant_src_nodes = (right_consonant_node,) if right_consonant_node is not None else ()
        state.last_right_alt_consonant_nodes = (right_alt_consonant_node,) if right_alt_consonant_node is not None else ()


        state.left_consonant_src_nodes = ()


    @enumerator.complete.listen
    def _():
        if len(state.right_consonant_src_nodes) == 0:
            # The outline contains no vowels and is likely a brief
            return
        
        state.trie.set_translation(state.right_consonant_src_nodes[0], state.translation)


    return hooks