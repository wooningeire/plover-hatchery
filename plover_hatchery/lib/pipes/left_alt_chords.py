from plover_hatchery.lib.pipes.Plugin import Plugin


from typing import Any, Callable, Generator, Protocol, final
from dataclasses import dataclass

from plover.steno import Stroke

from ..sopheme import Sound
from .banks import banks, BanksState
from .join import NodeSrc, join_on_strokes
from .Plugin import define_plugin, GetPluginApi
from .Hook import Hook


@final
class LeftAltChordsHooks:
    class OnCompleteVowel(Protocol):
        def __call__(self,
            *,
            left_alt_chords_state: "LeftAltChordsState",
            banks_state: BanksState,
        ) -> None: ...

    complete_vowel = Hook(OnCompleteVowel)


@final
@dataclass
class LeftAltChordsState:
    newest_left_alt_node: "int | None" = None
    last_left_alt_node: "int | None" = None
    """The latest node constructed by adding the alternate chord for a left consonant"""


def left_alt_chords(chords: Callable[[Sound], Generator[Stroke, None, None]]) -> Plugin[LeftAltChordsHooks]:
    @define_plugin(left_alt_chords)
    def plugin(get_plugin_api: GetPluginApi, **_):
        hooks = LeftAltChordsHooks()
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.begin.listen(left_alt_chords)
        def _():
            return LeftAltChordsState()
        

        @banks_hooks.before_complete_consonant.listen(left_alt_chords)
        def _(state: LeftAltChordsState, banks_state: BanksState, consonant: Sound, **_):
            # if len(last_left_alt_nodes) > 0:
            #     for left_stroke in left_strokes:
            #         state.trie.link_chain(
            #             last_left_alt_nodes[0], left_node, left_stroke.keys(),
            #             TransitionCostInfo(amphitheory.spec.TransitionCosts.ALT_CONSONANT + (amphitheory.spec.TransitionCosts.VOWEL_ELISION if state.is_first_consonant else 0), state.translation)
            #         )

            

            left_alt_node = join_on_strokes(banks_state.trie, banks_state.left_srcs, chords(consonant), banks_state.translation)
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

        
        @banks_hooks.complete_consonant.listen(left_alt_chords)
        def _(state: LeftAltChordsState, banks_state: BanksState, **_):
            state.last_left_alt_node = state.newest_left_alt_node

            if state.last_left_alt_node is None: return
            banks_state.left_srcs += (NodeSrc(state.last_left_alt_node, 3),)

        
        @banks_hooks.complete_vowel.listen(left_alt_chords)
        def _(state: LeftAltChordsState, banks_state: BanksState, **_):
            for handler in hooks.complete_vowel.handlers():
                handler(
                    left_alt_chords_state=state,
                    banks_state=banks_state,
                )


        return hooks

    return plugin