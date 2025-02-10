from plover_hatchery.lib.pipes.Plugin import Plugin


from typing import Any, Callable, Generator, Protocol, final
from dataclasses import dataclass

from plover.steno import Stroke

from ..sopheme import Sound
from .banks import banks, BanksState
from .join import NodeSrc, join_on_strokes, tuplify
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
    last_left_alt_nodes: tuple[NodeSrc, ...] = ()
    """Collection of left alt nodes since which only vowels, optional sounds, or silent sounds have occurred."""


def left_alt_chords(chords: Callable[[Sound], Generator[Stroke, None, None]]) -> Plugin[LeftAltChordsHooks]:
    @define_plugin(left_alt_chords)
    def plugin(get_plugin_api: GetPluginApi, **_):
        hooks = LeftAltChordsHooks()
        banks_api = get_plugin_api(banks)


        @banks_api.begin.listen(left_alt_chords)
        def _():
            return LeftAltChordsState()
        

        @banks_api.before_complete_consonant.listen(left_alt_chords)
        def _(state: LeftAltChordsState, banks_state: BanksState, consonant: Sound, **_):
            left_alt_node = join_on_strokes(banks_state.trie, banks_state.left_srcs, chords(consonant), banks_state.entry_id)


            state.newest_left_alt_node = left_alt_node

        
        @banks_api.complete_consonant.listen(left_alt_chords)
        def _(state: LeftAltChordsState, banks_state: BanksState, consonant: Sound, **_):
            new_last_left_alt_nodes = tuplify(state.newest_left_alt_node, 3)

            if not consonant.keysymbol.optional:
                state.last_left_alt_nodes = new_last_left_alt_nodes

            else:
                state.last_left_alt_nodes += new_last_left_alt_nodes


            banks_state.left_srcs += new_last_left_alt_nodes

        
        @banks_api.complete_vowel.listen(left_alt_chords)
        def _(state: LeftAltChordsState, banks_state: BanksState, **_):
            for handler in hooks.complete_vowel.handlers():
                handler(
                    left_alt_chords_state=state,
                    banks_state=banks_state,
                )


        return hooks

    return plugin