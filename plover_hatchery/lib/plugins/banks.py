from collections.abc import Iterable
from typing import Callable, TypeVar, Protocol, Any
from dataclasses import dataclass
import dataclasses

from plover.steno import Stroke

from ..sopheme import Sound
from ..trie import NondeterministicTrie, TransitionCostInfo
from ..config import TRIE_STROKE_BOUNDARY_KEY
from .state import OutlineSounds
from .join import NodeSrc, join_on_strokes, tuplify
from .consonants_vowels_enumeration import consonants_vowels_enumeration
from .Hook import Hook
from .Plugin import GetPluginApi, Plugin, define_plugin

@dataclass
class BanksState:
    trie: NondeterministicTrie[str, int]
    sounds: OutlineSounds
    entry_id: int

    plugin_states: dict[int, Any]

    group_index: int
    sound_index: int

    left_srcs: tuple[NodeSrc, ...]
    mid_srcs: tuple[NodeSrc, ...]
    right_srcs: tuple[NodeSrc, ...]

    # translation_candidates: tuple[NodeSrc, ...]

    last_left_node: "int | None" = None
    last_right_node: "int | None" = None


    def clone(self):
        return dataclasses.replace(self)


T = TypeVar("T")

@dataclass
class BanksHooks:
    class Begin(Protocol):
        def __call__(self) -> Any: ...
    class BeforeCompleteConsonant(Protocol):
        def __call__(self,
            *,
            state: Any,
            banks_state: BanksState,
            consonant: Sound,
            left_node: "int | None",
            right_node: "int | None",
        ) -> None: ...
    class CompleteConsonant(Protocol):
        def __call__(self,
            *,
            state: Any,
            banks_state: BanksState,
            consonant: Sound,
        ) -> None: ...
    class BeforeCompleteVowel(Protocol):
        def __call__(self,
            *,
            state: Any,
            banks_state: BanksState,
            mid_node: "int | None",
            new_stroke_node: "int | None",
            group_index: int,
            sound_index: int,
        ) -> None: ...
    class CompleteVowel(Protocol):
        def __call__(self,
            *,
            state: Any,
            banks_state: BanksState,
            mid_node: "int | None",
            new_stroke_node: "int | None",
            group_index: int,
            sound_index: int,
        ) -> None: ...

    begin = Hook(Begin)
    before_complete_consonant = Hook(BeforeCompleteConsonant)
    complete_consonant = Hook(CompleteConsonant)
    before_complete_vowel = Hook(BeforeCompleteVowel)
    complete_vowel = Hook(CompleteVowel)


def banks(
    *,
    left_chords: Callable[[Sound], Iterable[Stroke]],
    mid_chords: Callable[[Sound], Iterable[Stroke]],
    right_chords: Callable[[Sound], Iterable[Stroke]],
) -> Plugin[BanksHooks]:
    @define_plugin(banks)
    def plugin(get_plugin_api: GetPluginApi, **_):
        hooks = BanksHooks()

        def on_begin_hook():
            states: dict[int, Any] = {}
            for plugin_id, handler in hooks.begin.ids_handlers():
                states[plugin_id] = handler()

            return states

        def on_before_complete_consonant(banks_state: BanksState, consonant: Sound, left_node: "int | None", right_node: "int | None"):
            for plugin_id, handler in hooks.before_complete_consonant.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    consonant=consonant,
                    left_node=left_node,
                    right_node=right_node,
                )

        def on_complete_consonant(banks_state: BanksState, consonant: Sound):
            for plugin_id, handler in hooks.complete_consonant.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    consonant=consonant,
                )

        def on_before_complete_vowel(
            banks_state: BanksState,
            mid_node: "int | None",
            new_stroke_node: "int | None",
            group_index: int,
            sound_index: int,
        ):
            for plugin_id, handler in hooks.before_complete_vowel.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    mid_node=mid_node,
                    new_stroke_node=new_stroke_node,
                    group_index=group_index,
                    sound_index=sound_index,
                )

        def on_complete_vowel(
            banks_state: BanksState,
            mid_node: "int | None",
            new_stroke_node: "int | None",
            group_index: int,
            sound_index: int,
        ):
            for plugin_id, handler in hooks.complete_vowel.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    mid_node=mid_node,
                    new_stroke_node=new_stroke_node,
                    group_index=group_index,
                    sound_index=sound_index,
                )


        consonants_vowels_enumeration_hooks = get_plugin_api(consonants_vowels_enumeration)


        @consonants_vowels_enumeration_hooks.begin.listen(banks)
        def _(trie: NondeterministicTrie[str, int], sounds: OutlineSounds, entry_id: int):
            left_src_nodes = (NodeSrc(trie.ROOT, 0),)

            return BanksState(
                trie,
                sounds,
                entry_id,

                group_index=0,
                sound_index=0,

                left_srcs=left_src_nodes,
                mid_srcs=left_src_nodes,
                right_srcs=(),
                # translation_candidates=(),

                plugin_states=on_begin_hook(),
            )


        @consonants_vowels_enumeration_hooks.consonant.listen(banks)
        def _(state: BanksState, consonant: Sound, group_index: int, sound_index: int, **_):
            state.group_index = group_index
            state.sound_index = sound_index


            left_node = join_on_strokes(state.trie, state.left_srcs, left_chords(consonant), state.entry_id)
            right_node = join_on_strokes(state.trie, state.right_srcs, right_chords(consonant), state.entry_id)


            on_before_complete_consonant(state, consonant, left_node, right_node)


            state.left_srcs = tuplify(left_node)
            state.mid_srcs = state.left_srcs
            state.right_srcs = tuplify(right_node)
            # state.translation_candidates = state.right_srcs

            state.last_left_node = left_node
            state.last_right_node = right_node


            on_complete_consonant(state, consonant)

        
        @consonants_vowels_enumeration_hooks.vowel.listen(banks)
        def _(state: BanksState, vowel: Sound, group_index: int, sound_index: int):
            state.group_index = group_index
            state.sound_index = sound_index


            mid_node = join_on_strokes(state.trie, state.mid_srcs, mid_chords(vowel), state.entry_id)


            if mid_node is not None:
                new_stroke_node = state.trie.follow(mid_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.entry_id))
            else:
                new_stroke_node = None


            on_before_complete_vowel(state, mid_node, new_stroke_node, group_index, sound_index)


            state.left_srcs = tuplify(new_stroke_node)
            state.mid_srcs = state.left_srcs
            state.right_srcs = tuplify(mid_node)
            # state.translation_candidates = state.right_srcs


            on_complete_vowel(state, mid_node, new_stroke_node, group_index, sound_index)


        @consonants_vowels_enumeration_hooks.complete.listen(banks)
        def _(state: BanksState):
            for right_src in state.right_srcs:
                state.trie.set_translation(right_src.node, state.entry_id)


        return hooks
    
    return plugin