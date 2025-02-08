from typing import Callable, Generator, Protocol, TypeVar
from dataclasses import dataclass

from plover.steno import Stroke

from ..trie import TransitionCostInfo, NondeterministicTrie
from ..sophone.Sophone import Sophone
from ..sopheme import Sound
from ..theory_defaults.amphitheory import amphitheory
from .banks import BanksHooks, BanksState
from .join import join_on_strokes


T = TypeVar("T")

@dataclass
class LeftAltChordsPlugin:
    class OnCompleteVowel(Protocol):
        def __call__(self,
            *,
            left_alt_chords_state: "LeftAltChordsState",
            banks_state: BanksState,
        ) -> None: ...

    on_complete_vowel: OnCompleteVowel


@dataclass
class LeftAltChordsState:
    newest_left_alt_node: "int | None" = None
    last_left_alt_node: "int | None" = None
    """The latest node constructed by adding the alternate chord for a left consonant"""


def left_alt_chords(
    *plugins: LeftAltChordsPlugin,
    chords: Callable[[Sound], Generator[Stroke, None, None]],
):
    def on_begin():
        return LeftAltChordsState()
    

    def on_before_complete_consonant(state: LeftAltChordsState, banks_state: BanksState, consonant: Sound, **_):
        # if len(last_left_alt_nodes) > 0:
        #     for left_stroke in left_strokes:
        #         state.trie.link_chain(
        #             last_left_alt_nodes[0], left_node, left_stroke.keys(),
        #             TransitionCostInfo(amphitheory.spec.TransitionCosts.ALT_CONSONANT + (amphitheory.spec.TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0), state.translation)
        #         )

        

        left_alt_node = join_on_strokes(banks_state.trie, banks_state.left_src_nodes, chords(consonant), banks_state.translation)
        # if len(state.left_elision_boundary_src_nodes) > 0:
        #     state.trie.link_chain(state.left_elision_boundary_src_nodes[0], left_alt_consonant_node, left_alt_stroke_keys, TransitionCostInfo(0, state.translation))

        # if len(last_left_alt_nodes) > 0:
        #     state.trie.link_chain(
        #         last_left_alt_nodes[0], left_alt_consonant_node, left_alt_stroke_keys,
        #         TransitionCostInfo(amphitheory.spec.TransitionCosts.ALT_CONSONANT + (amphitheory.spec.TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0), state.translation)
        #     )

        # if state.can_elide_prev_vowel_left:
        #     # uses original left consonant node because it is ok to continue onto the vowel if the previous consonant is present
        #     state.left_squish_elision.execute(state.trie, state.translation, left_node, left_alt_stroke, amphitheory.spec.TransitionCosts.ALT_CONSONANT)

        #     state.left_squish_elision.execute(state.trie, state.translation, left_alt_consonant_node, left_alt_stroke, amphitheory.spec.TransitionCosts.ALT_CONSONANT)
        #     state.boundary_elision.execute(state.trie, state.translation, left_alt_consonant_node, left_alt_stroke, amphitheory.spec.TransitionCosts.ALT_CONSONANT)


        state.newest_left_alt_node = left_alt_node

    
    def on_complete_consonant(state: LeftAltChordsState, banks_state: BanksState, **_):
        if state.newest_left_alt_node is None: return
        state.last_left_alt_node = state.newest_left_alt_node

        banks_state.left_src_nodes += (state.last_left_alt_node,)

    
    def on_complete_vowel(state: LeftAltChordsState, banks_state: BanksState, **_):
        for plugin in plugins:
            plugin.on_complete_vowel(
                left_alt_chords_state=state,
                banks_state=banks_state,
            )

    
    return BanksHooks(
        on_begin=on_begin,
        on_before_complete_consonant=on_before_complete_consonant,
        on_complete_consonant=on_complete_consonant,
        on_complete_vowel=on_complete_vowel,
    )
