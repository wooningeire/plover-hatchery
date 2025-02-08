from typing import Callable, Generator, TypeVar, Protocol, Generic, Any
from dataclasses import dataclass

from plover.steno import Stroke

from ..sopheme import Sound
from ..sophone.Sophone import Sophone
from ..trie import NondeterministicTrie, TransitionCostInfo
from ..config import TRIE_STROKE_BOUNDARY_KEY, TRIE_LINKER_KEY
from ..theory_defaults.amphitheory import amphitheory
from .state import EntryBuilderState, OutlineSounds, ConsonantVowelGroup
from .join import join, join_on_strokes, tuplify
from .consonants_vowels_enumeration import ConsonantsVowelsEnumerationHooks
from .Hook import Hook, HookAttr
from .Plugin import Plugin, GetPlugin

@dataclass
class BanksState:
    trie: NondeterministicTrie[str, str]
    sounds: OutlineSounds
    translation: str

    plugin_states: dict[int, Any]

    left_src_nodes: tuple[int, ...]
    mid_src_nodes: tuple[int, ...]
    right_src_nodes: tuple[int, ...]

    last_left_node: "int | None" = None
    last_right_node: "int | None" = None


T = TypeVar("T")
U = TypeVar("U")

@dataclass
class BanksHooks(Generic[T]):
    class OnBegin(Protocol[U]):
        def __call__(self) -> U: ...
    class OnBeforeCompleteConsonant(Protocol[U]):
        def __call__(self,
            *,
            state: U,
            banks_state: BanksState,
            consonant: Sound,
        ) -> None: ...
    class OnCompleteConsonant(Protocol[U]):
        def __call__(self,
            *,
            state: U,
            banks_state: BanksState,
            consonant: Sound,
        ) -> None: ...
    class OnCompleteVowel(Protocol[U]):
        def __call__(self,
            *,
            state: U,
            banks_state: BanksState,
            mid_node: int,
            new_stroke_node: int,
            group_index: int,
            sound_index: int,
        ) -> None: ...

    on_begin = HookAttr(OnBegin[T])
    on_before_complete_consonant = HookAttr(OnBeforeCompleteConsonant[T])
    on_complete_consonant = HookAttr(OnCompleteConsonant[T])
    on_complete_vowel = HookAttr(OnCompleteVowel[T])


def banks(
    *,
    left_chords: Callable[[Sound], Generator[Stroke, None, None]],
    mid_chords: Callable[[Sound], Generator[Stroke, None, None]],
    right_chords: Callable[[Sound], Generator[Stroke, None, None]],
):
    this_id = id(banks)


    @Plugin.define
    def initialize(base_hooks: ConsonantsVowelsEnumerationHooks, **_):
        hooks = BanksHooks()

        def on_begin_hook():
            states: dict[int, Any] = {}
            for plugin_id, handler in hooks.on_begin.ids_handlers():
                states[plugin_id] = handler()

            return states

        def on_before_complete_consonant(banks_state: BanksState, consonant: Sound):
            for plugin_id, handler in hooks.on_before_complete_consonant.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    consonant=consonant
                )

        def on_complete_consonant(banks_state: BanksState, consonant: Sound):
            for plugin_id, handler in hooks.on_complete_consonant.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    consonant=consonant
                )

        def on_complete_vowel(
            banks_state: BanksState,
            mid_node: int,
            new_stroke_node: int,
            group_index: int,
            sound_index: int,
        ):
            for plugin_id, handler in hooks.on_complete_vowel.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    mid_node=mid_node,
                    new_stroke_node=new_stroke_node,
                    group_index=group_index,
                    sound_index=sound_index,
                )


        @base_hooks.on_begin.listen(this_id)
        def _(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
            left_src_nodes = (trie.ROOT,)

            return BanksState(
                trie,
                sounds,
                translation,

                left_src_nodes=left_src_nodes,
                mid_src_nodes=left_src_nodes,
                right_src_nodes=(),

                plugin_states=on_begin_hook(),
            )


        @base_hooks.on_consonant.listen(this_id)
        def _(state: BanksState, consonant: Sound, **_):
            left_node = join_on_strokes(state.trie, state.left_src_nodes, left_chords(consonant), state.translation)
            right_node = join_on_strokes(state.trie, state.right_src_nodes, right_chords(consonant), state.translation)

            if left_node is not None and right_node is not None:
                state.trie.link(right_node, left_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.translation))


            on_before_complete_consonant(state, consonant)


            state.left_src_nodes = tuplify(left_node)
            state.mid_src_nodes = state.left_src_nodes
            state.right_src_nodes = tuplify(right_node)

            state.last_left_node = left_node
            state.last_right_node = right_node


            on_complete_consonant(state, consonant)

        
        @base_hooks.on_vowel.listen(this_id)
        def _(state: BanksState, vowel: Sound, group_index: int, sound_index: int):
            mid_node = join(state.trie, state.mid_src_nodes, (stroke.rtfcre for stroke in mid_chords(vowel)), state.translation)


            if mid_node is not None:
                new_stroke_node = state.trie.get_first_dst_node_else_create(mid_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.translation))
            else:
                new_stroke_node = None


            state.left_src_nodes = tuplify(new_stroke_node)
            state.mid_src_nodes = state.left_src_nodes
            state.right_src_nodes += tuplify(mid_node)

            if mid_node is not None and new_stroke_node is not None:
                on_complete_vowel(state, mid_node, new_stroke_node, group_index, sound_index)


        @base_hooks.on_complete.listen(this_id)
        def _(state: BanksState):
            for right_src_node in state.right_src_nodes:
                state.trie.set_translation(right_src_node, state.translation)


        return hooks
    
    return initialize