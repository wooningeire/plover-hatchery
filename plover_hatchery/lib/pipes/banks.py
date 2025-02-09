from plover_hatchery.lib.pipes.Plugin import Plugin


from typing import Callable, Generator, TypeVar, Protocol, Generic, Any
from dataclasses import dataclass
import dataclasses

from plover.steno import Stroke

from ..sopheme import Sound
from ..sophone.Sophone import Sophone
from ..trie import NondeterministicTrie, TransitionCostInfo
from ..config import TRIE_STROKE_BOUNDARY_KEY, TRIE_LINKER_KEY
from .state import OutlineSounds, ConsonantVowelGroup
from .join import join, join_on_strokes, tuplify
from .consonants_vowels_enumeration import ConsonantsVowelsEnumerationHooks
from .Hook import Hook
from .Plugin import Plugin, define_plugin

@dataclass
class BanksState:
    trie: NondeterministicTrie[str, str]
    sounds: OutlineSounds
    translation: str

    plugin_states: dict[int, Any]

    group_index: int
    sound_index: int

    left_src_nodes: tuple[int, ...]
    mid_src_nodes: tuple[int, ...]
    right_src_nodes: tuple[int, ...]

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
    left_chords: Callable[[Sound], Generator[Stroke, None, None]],
    mid_chords: Callable[[Sound], Generator[Stroke, None, None]],
    right_chords: Callable[[Sound], Generator[Stroke, None, None]],
) -> Plugin[BanksHooks]:
    @define_plugin(banks)
    def plugin(base_hooks: ConsonantsVowelsEnumerationHooks[BanksState], **_):
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


        @base_hooks.begin.listen(banks)
        def _(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
            left_src_nodes = (trie.ROOT,)

            return BanksState(
                trie,
                sounds,
                translation,

                group_index=0,
                sound_index=0,

                left_src_nodes=left_src_nodes,
                mid_src_nodes=left_src_nodes,
                right_src_nodes=(),

                plugin_states=on_begin_hook(),
            )


        @base_hooks.consonant.listen(banks)
        def _(state: BanksState, consonant: Sound, group_index: int, sound_index: int, **_):
            state.group_index = group_index
            state.sound_index = sound_index


            left_node = join_on_strokes(state.trie, state.left_src_nodes, left_chords(consonant), state.translation)
            right_node = join_on_strokes(state.trie, state.right_src_nodes, right_chords(consonant), state.translation)


            on_before_complete_consonant(state, consonant, left_node, right_node)


            state.left_src_nodes = tuplify(left_node)
            state.mid_src_nodes = state.left_src_nodes
            state.right_src_nodes = tuplify(right_node)

            state.last_left_node = left_node
            state.last_right_node = right_node


            on_complete_consonant(state, consonant)

        
        @base_hooks.vowel.listen(banks)
        def _(state: BanksState, vowel: Sound, group_index: int, sound_index: int):
            state.group_index = group_index
            state.sound_index = sound_index


            mid_node = join_on_strokes(state.trie, state.mid_src_nodes, mid_chords(vowel), state.translation)


            if mid_node is not None:
                new_stroke_node = state.trie.get_first_dst_node_else_create(mid_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.translation))
            else:
                new_stroke_node = None


            on_before_complete_vowel(state, mid_node, new_stroke_node, group_index, sound_index)


            state.left_src_nodes = tuplify(new_stroke_node)
            state.mid_src_nodes = state.left_src_nodes
            state.right_src_nodes += tuplify(mid_node)


            on_complete_vowel(state, mid_node, new_stroke_node, group_index, sound_index)


        @base_hooks.complete.listen(banks)
        def _(state: BanksState):
            for right_src_node in state.right_src_nodes:
                state.trie.set_translation(right_src_node, state.translation)


        return hooks
    
    return plugin