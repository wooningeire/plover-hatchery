from plover_hatchery.lib.pipes.Plugin import Plugin


from typing import Any, Callable, Protocol, final
from collections.abc import Generator
from dataclasses import dataclass

from plover.steno import Stroke

from ..sopheme import Sound
from .banks import banks, BanksState
from .join import NodeSrc, join_on_strokes, tuplify
from .Plugin import define_plugin, GetPluginApi
from .Hook import Hook


@final
class RightAltChordsHooks:
    class OnCompleteVowel(Protocol):
        def __call__(self,
            *,
            right_alt_chords_state: "RightAltChordsState",
            banks_state: BanksState,
        ) -> None: ...

    complete_vowel = Hook(OnCompleteVowel)


@final
@dataclass
class RightAltChordsState:
    newest_right_alt_node: "int | None" = None
    last_right_alt_nodes: tuple[NodeSrc, ...] = ()
    """The latest node constructed by adding the alternate chord for a left consonant"""


def right_alt_chords(chords: Callable[[Sound], Generator[Stroke, None, None]]) -> Plugin[RightAltChordsHooks]:
    @define_plugin(right_alt_chords)
    def plugin(get_plugin_api: GetPluginApi, **_):
        hooks = RightAltChordsHooks()
        banks_hooks = get_plugin_api(banks)


        @banks_hooks.begin.listen(right_alt_chords)
        def _():
            return RightAltChordsState()
        

        @banks_hooks.before_complete_consonant.listen(right_alt_chords)
        def _(state: RightAltChordsState, banks_state: BanksState, consonant: Sound, **_):
            right_alt_node = join_on_strokes(banks_state.trie, banks_state.right_srcs, chords(consonant), banks_state.entry_id)

            state.newest_right_alt_node = right_alt_node

        
        @banks_hooks.complete_consonant.listen(right_alt_chords)
        def _(state: RightAltChordsState, banks_state: BanksState, consonant: Sound, **_):
            new_last_right_alt_nodes = tuplify(state.newest_right_alt_node, 3)

            if not consonant.keysymbol.optional:
                state.last_right_alt_nodes = new_last_right_alt_nodes

            else:
                state.last_right_alt_nodes += new_last_right_alt_nodes


            banks_state.right_srcs += new_last_right_alt_nodes

        
        @banks_hooks.complete_vowel.listen(right_alt_chords)
        def _(state: RightAltChordsState, banks_state: BanksState, **_):
            for handler in hooks.complete_vowel.handlers():
                handler(
                    right_alt_chords_state=state,
                    banks_state=banks_state,
                )


        return hooks

    return plugin