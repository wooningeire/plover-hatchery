from collections.abc import Iterable
from typing import Callable, TypeVar, Protocol, Any, final
from dataclasses import dataclass
import dataclasses

from plover.steno import Stroke

from plover_hatchery.lib.sopheme import Keysymbol, Sopheme, SophemeSeq, SophemeSeqPhoneme

from ..trie import NondeterministicTrie, TransitionCostInfo
from ..config import TRIE_STROKE_BOUNDARY_KEY
from .join import NodeSrc, join_on_strokes, tuplify
from .consonants_vowels_enumeration import consonants_vowels_enumeration
from .Hook import Hook
from .Plugin import GetPluginApi, Plugin, define_plugin


@final
@dataclass
class BanksState:
    trie: NondeterministicTrie[str, int]
    sophemes: SophemeSeq
    entry_id: int

    plugin_states: dict[int, Any]

    current_phoneme: "SophemeSeqPhoneme | None"

    left_srcs: tuple[NodeSrc, ...]
    mid_srcs: tuple[NodeSrc, ...]
    right_srcs: tuple[NodeSrc, ...]

    # translation_candidates: tuple[NodeSrc, ...]

    last_left_nodes: tuple[NodeSrc, ...] = ()
    """Collection of left nodes since which only vowels, optional sounds, or silent sounds have occurred."""
    last_right_nodes: tuple[NodeSrc, ...] = ()
    """Collection of right nodes since which only vowels, optional sounds, or silent sounds have occurred."""


    def clone(self):
        return dataclasses.replace(self)


T = TypeVar("T")

@final
@dataclass
class BanksApi:
    class Begin(Protocol):
        def __call__(self) -> Any: ...
    class BeginConsonant(Protocol):
        def __call__(self,
            *,
            state: Any,
            banks_state: BanksState,
            phoneme: SophemeSeqPhoneme,
        ) -> None: ...
    class BeforeCompleteConsonant(Protocol):
        def __call__(self,
            *,
            state: Any,
            banks_state: BanksState,
            phoneme: SophemeSeqPhoneme,
            left_node: "int | None",
            right_node: "int | None",
        ) -> None: ...
    class CompleteConsonant(Protocol):
        def __call__(self,
            *,
            state: Any,
            banks_state: BanksState,
            phoneme: SophemeSeqPhoneme,
        ) -> None: ...
    class BeginVowel(Protocol):
        def __call__(self,
            *,
            state: Any,
            banks_state: BanksState,
            phoneme: SophemeSeqPhoneme,
        ) -> None: ...
    class BeforeCompleteVowel(Protocol):
        def __call__(self,
            *,
            state: Any,
            banks_state: BanksState,
            mid_node: "int | None",
            new_stroke_node: "int | None",
            phoneme: SophemeSeqPhoneme,
        ) -> None: ...
    class CompleteVowel(Protocol):
        def __call__(self,
            *,
            state: Any,
            banks_state: BanksState,
            mid_node: "int | None",
            new_stroke_node: "int | None",
            phoneme: SophemeSeqPhoneme,
        ) -> None: ...

    left_chords: Callable[[SophemeSeqPhoneme], Iterable[Stroke]]
    mid_chords: Callable[[SophemeSeqPhoneme], Iterable[Stroke]]
    right_chords: Callable[[SophemeSeqPhoneme], Iterable[Stroke]]

    begin = Hook(Begin)
    begin_consonant = Hook(BeginConsonant)
    before_complete_consonant = Hook(BeforeCompleteConsonant)
    complete_consonant = Hook(CompleteConsonant)
    begin_vowel = Hook(BeginVowel)
    before_complete_vowel = Hook(BeforeCompleteVowel)
    complete_vowel = Hook(CompleteVowel)


def banks(
    *,
    left_chords: Callable[[SophemeSeqPhoneme], Iterable[Stroke]],
    mid_chords: Callable[[SophemeSeqPhoneme], Iterable[Stroke]],
    right_chords: Callable[[SophemeSeqPhoneme], Iterable[Stroke]],
) -> Plugin[BanksApi]:
    @define_plugin(banks)
    def plugin(get_plugin_api: GetPluginApi, **_):
        hooks = BanksApi(left_chords, mid_chords, right_chords)

        def on_begin_hook():
            states: dict[int, Any] = {}
            for plugin_id, handler in hooks.begin.ids_handlers():
                states[plugin_id] = handler()

            return states

        def on_begin_consonant(
            banks_state: BanksState,
            phoneme: SophemeSeqPhoneme,
        ):
            for plugin_id, handler in hooks.begin_consonant.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    phoneme=phoneme,
                )

        def on_before_complete_consonant(banks_state: BanksState, phoneme: SophemeSeqPhoneme, left_node: "int | None", right_node: "int | None"):
            for plugin_id, handler in hooks.before_complete_consonant.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    phoneme=phoneme,
                    left_node=left_node,
                    right_node=right_node,
                )

        def on_complete_consonant(banks_state: BanksState, phoneme: SophemeSeqPhoneme):
            for plugin_id, handler in hooks.complete_consonant.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    phoneme=phoneme,
                )

        def on_begin_vowel(
            banks_state: BanksState,
            phoneme: SophemeSeqPhoneme,
        ):
            for plugin_id, handler in hooks.begin_vowel.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    phoneme=phoneme,
                )
                

        def on_before_complete_vowel(
            banks_state: BanksState,
            mid_node: "int | None",
            new_stroke_node: "int | None",
            phoneme: SophemeSeqPhoneme,
        ):
            for plugin_id, handler in hooks.before_complete_vowel.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    mid_node=mid_node,
                    new_stroke_node=new_stroke_node,
                    phoneme=phoneme,
                )

        def on_complete_vowel(
            banks_state: BanksState,
            mid_node: "int | None",
            new_stroke_node: "int | None",
            phoneme: SophemeSeqPhoneme,
        ):
            for plugin_id, handler in hooks.complete_vowel.ids_handlers():
                handler(
                    state=banks_state.plugin_states.get(plugin_id),
                    banks_state=banks_state,
                    mid_node=mid_node,
                    new_stroke_node=new_stroke_node,
                    phoneme=phoneme,
                )


        consonants_vowels_enumeration_hooks = get_plugin_api(consonants_vowels_enumeration)


        @consonants_vowels_enumeration_hooks.begin.listen(banks)
        def _(trie: NondeterministicTrie[str, int], sophemes: SophemeSeq, entry_id: int):
            left_src_nodes = (NodeSrc(trie.ROOT, 0),)

            return BanksState(
                trie,
                sophemes,
                entry_id,

                left_srcs=left_src_nodes,
                mid_srcs=left_src_nodes,
                right_srcs=(),

                plugin_states=on_begin_hook(),

                current_phoneme=sophemes.first_phoneme(),
            )


        @consonants_vowels_enumeration_hooks.consonant.listen(banks)
        def _(state: BanksState, phoneme: SophemeSeqPhoneme, **_):
            state.current_phoneme = phoneme


            on_begin_consonant(state, phoneme)


            left_node = join_on_strokes(state.trie, state.left_srcs, left_chords(phoneme), state.entry_id).dst_node_id
            right_node = join_on_strokes(state.trie, state.right_srcs, right_chords(phoneme), state.entry_id).dst_node_id


            on_before_complete_consonant(state, phoneme, left_node, right_node)


            new_left_srcs = tuplify(left_node)
            new_mid_srcs = new_left_srcs
            new_right_srcs = tuplify(right_node)

            new_last_left_nodes = tuplify(left_node)
            new_last_right_nodes = tuplify(right_node)


            if not phoneme.keysymbol.optional:
                state.left_srcs = new_left_srcs
                state.mid_srcs = new_mid_srcs
                state.right_srcs = new_right_srcs

                state.last_left_nodes = new_last_left_nodes
                state.last_right_nodes = new_last_right_nodes

            else:
                state.left_srcs = (*NodeSrc.increment_costs(state.left_srcs, 15), *new_left_srcs)
                state.mid_srcs = (*NodeSrc.increment_costs(state.mid_srcs, 15), *new_mid_srcs)
                state.right_srcs = (*NodeSrc.increment_costs(state.right_srcs, 15), *new_right_srcs)

                state.last_left_nodes = (*NodeSrc.increment_costs(state.last_left_nodes, 15), *new_last_left_nodes)
                state.last_right_nodes = (*NodeSrc.increment_costs(state.last_right_nodes, 15), *new_last_right_nodes)


            on_complete_consonant(state, phoneme)

        
        @consonants_vowels_enumeration_hooks.vowel.listen(banks)
        def _(state: BanksState, phoneme: SophemeSeqPhoneme):
            state.current_phoneme = phoneme

            
            on_begin_vowel(state, phoneme)


            mid_node = join_on_strokes(state.trie, state.mid_srcs, mid_chords(phoneme), state.entry_id).dst_node_id
            

            if mid_node is not None:
                new_stroke_node = state.trie.follow(mid_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, state.entry_id)).dst_node_id
            else:
                new_stroke_node = None


            on_before_complete_vowel(state, mid_node, new_stroke_node, phoneme)


            new_left_srcs = tuplify(new_stroke_node)
            new_mid_srcs = new_left_srcs
            new_right_srcs = tuplify(mid_node)


            if not phoneme.keysymbol.optional:
                state.left_srcs = new_left_srcs
                state.mid_srcs = new_mid_srcs
                state.right_srcs = new_right_srcs

            else:
                state.left_srcs = (*NodeSrc.increment_costs(state.left_srcs, 8), *new_left_srcs)
                state.mid_srcs = (*NodeSrc.increment_costs(state.mid_srcs, 8), *new_mid_srcs)
                state.right_srcs = (*NodeSrc.increment_costs(state.right_srcs, 8), *new_right_srcs)


            on_complete_vowel(state, mid_node, new_stroke_node, phoneme)


        @consonants_vowels_enumeration_hooks.complete.listen(banks)
        def _(state: BanksState):
            for right_src in state.right_srcs:
                state.trie.set_translation(right_src.node, state.entry_id)


        return hooks
    
    return plugin