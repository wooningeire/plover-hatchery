from plover.steno import Stroke

from ..trie import TransitionCostInfo, NondeterministicTrie
from ..sophone.Sophone import Sophone
from ..theory_defaults.amphitheory import amphitheory

from .use_banks import BanksHooks
from .state import EntryBuilderState, ConsonantVowelGroup
from .Hook import Hook

class LeftChordsHooks:
    def __init__(self):
        self.node_created: Hook[EntryBuilderState, int, tuple[Stroke, ...], tuple[int, ...]] = Hook()
        self.complete_nonfinal_group: Hook[EntryBuilderState, tuple[int, ...]] = Hook()


def use_left_chords(manage_state: BanksHooks, chords_raw: dict[str, str]):
    chords = {
        Sophone.__dict__[key]: Stroke.from_steno(steno)
        for key, steno in chords_raw.items()
    }


    hooks = LeftChordsHooks()


    src_nodes: tuple[int, ...]
    """The node from which the next left consonant chord will be attached"""
    newest_left_node: "int | None"
    prev_left_nodes: tuple[int, ...]
    """The node constructed by adding the previous left consonant; can be empty if the previous phoneme was a vowel"""


    vowels_src_node: "int | None"


    @manage_state.begin.listen
    def _(trie: NondeterministicTrie[str, str]):
        nonlocal src_nodes
        nonlocal newest_left_node
        nonlocal prev_left_nodes

        src_nodes = (trie.ROOT,)
        newest_left_node = None
        prev_left_nodes = ()


    @manage_state.begin_nonfinal_group.listen
    def _(state: EntryBuilderState, group: ConsonantVowelGroup):
        nonlocal vowels_src_node


        # vowels_src_node = None
        # if len(group.consonants) == 0 and not state.is_first_consonant_set:
        #     vowels_src_node = state.trie.get_first_dst_node_else_create(
        #         state.left_consonant_src_nodes[0],
        #         TRIE_LINKER_KEY,
        #         TransitionCostInfo(0, state.translation)
        #     )


    @manage_state.begin_consonant.listen
    def _(state: EntryBuilderState):
        nonlocal newest_left_node


        if len(state.left_consonant_src_nodes) == 0:
            return

        
        left_consonant_node = None

        strokes = (
            *amphitheory.left_consonant_strokes(state.consonant),
            chords[amphitheory.sound_sophone(state.consonant)],
        )

        for stroke in strokes:
            if left_consonant_node is None:
                print(f"left src node = {state.left_consonant_src_nodes[0]}")
                left_consonant_node = state.trie.get_first_dst_node_else_create_chain(state.left_consonant_src_nodes[0], stroke.keys(), TransitionCostInfo(0, state.translation))
                print(f"created left node {left_consonant_node}")
            else:
                state.trie.link_chain(state.left_consonant_src_nodes[0], left_consonant_node, stroke.keys(), TransitionCostInfo(0, state.translation))


            # if len(state.left_elision_boundary_src_nodes) > 0:
            #     state.trie.link_chain(state.left_elision_boundary_src_nodes[0], left_consonant_node, left_stroke_keys, TransitionCostInfo(0, state.translation))


            if state.can_elide_prev_vowel_left:
                state.left_squish_elision.execute(state.trie, state.translation, left_consonant_node, stroke, 0)
                state.boundary_elision.execute(state.trie, state.translation, left_consonant_node, stroke, 0)


        assert left_consonant_node is not None


        hooks.node_created.emit(state, left_consonant_node, strokes, state.left_consonant_src_nodes)
            

        state.newest_left_consonant_node = newest_left_node = left_consonant_node


    @manage_state.complete_consonant_2.listen
    def _(state: EntryBuilderState, left_node: "int | None", right_node: "int | None"):
        nonlocal src_nodes
        nonlocal prev_left_nodes

        state.left_consonant_src_nodes = src_nodes = (newest_left_node,) if newest_left_node is not None else ()
        state.prev_left_consonant_nodes = prev_left_nodes = (newest_left_node,) if newest_left_node is not None else ()


    @manage_state.complete_nonfinal_group.listen
    def _(state: EntryBuilderState, group: ConsonantVowelGroup, new_stroke_node: int):
        nonlocal src_nodes
        nonlocal prev_left_nodes


        hooks.complete_nonfinal_group.emit(state, src_nodes)


        state.left_consonant_src_nodes = src_nodes = (new_stroke_node,)
        state.prev_left_consonant_nodes = prev_left_nodes = ()


    return hooks