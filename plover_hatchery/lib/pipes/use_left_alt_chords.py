from plover.steno import Stroke

from ..trie import TransitionCostInfo, NondeterministicTrie
from ..sophone.Sophone import Sophone
from ..theory_defaults.amphitheory import amphitheory

from .state import EntryBuilderState, ConsonantVowelGroup


def use_left_alt_chords(manage_state: BanksHooks, chords_raw: dict[str, str]):
    chords = {
        Sophone.__dict__[key]: Stroke.from_steno(steno)
        for key, steno in chords_raw.items()
    }


    newest_left_alt_node: "int | None"
    last_left_alt_nodes: tuple[int, ...]
    """The latest node constructed by adding the alternate chord for a left consonant"""


    @manage_state.begin.listen
    def _(trie: NondeterministicTrie[str, str]):
        nonlocal newest_left_alt_node
        nonlocal last_left_alt_nodes

        newest_left_alt_node = None
        last_left_alt_nodes = ()


    @manage_state.left_node_created.listen
    def _(state: EntryBuilderState, left_node: int, left_strokes: tuple[Stroke, ...], src_nodes: tuple[int, ...]):
        nonlocal newest_left_alt_node


        if len(last_left_alt_nodes) > 0:
            for left_stroke in left_strokes:
                state.trie.link_chain(
                    last_left_alt_nodes[0], left_node, left_stroke.keys(),
                    TransitionCostInfo(amphitheory.spec.TransitionCosts.ALT_CONSONANT + (amphitheory.spec.TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0), state.translation)
                )




        sophone = amphitheory.sound_sophone(state.consonant)
        if len(src_nodes) == 0 or sophone not in chords:
            return
        
        left_alt_stroke = chords[sophone]


        left_alt_stroke_keys = left_alt_stroke.keys()

        left_alt_consonant_node = state.trie.get_first_dst_node_else_create_chain(src_nodes[0], left_alt_stroke_keys, TransitionCostInfo(amphitheory.spec.TransitionCosts.ALT_CONSONANT, state.translation))
        # if len(state.left_elision_boundary_src_nodes) > 0:
        #     state.trie.link_chain(state.left_elision_boundary_src_nodes[0], left_alt_consonant_node, left_alt_stroke_keys, TransitionCostInfo(0, state.translation))

        if len(last_left_alt_nodes) > 0:
            state.trie.link_chain(
                last_left_alt_nodes[0], left_alt_consonant_node, left_alt_stroke_keys,
                TransitionCostInfo(amphitheory.spec.TransitionCosts.ALT_CONSONANT + (amphitheory.spec.TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0), state.translation)
            )

        if state.can_elide_prev_vowel_left:
            # uses original left consonant node because it is ok to continue onto the vowel if the previous consonant is present
            state.left_squish_elision.execute(state.trie, state.translation, left_node, left_alt_stroke, amphitheory.spec.TransitionCosts.ALT_CONSONANT)

            state.left_squish_elision.execute(state.trie, state.translation, left_alt_consonant_node, left_alt_stroke, amphitheory.spec.TransitionCosts.ALT_CONSONANT)
            state.boundary_elision.execute(state.trie, state.translation, left_alt_consonant_node, left_alt_stroke, amphitheory.spec.TransitionCosts.ALT_CONSONANT)


        newest_left_alt_node = left_alt_consonant_node

    
    @manage_state.complete_consonant_2.listen
    def _(state: EntryBuilderState, left_node: "int | None", right_node: "int | None"):
        nonlocal last_left_alt_nodes

        last_left_alt_nodes = (newest_left_alt_node,) if newest_left_alt_node is not None else ()
