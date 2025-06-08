from collections.abc import Callable
from dataclasses import dataclass
from typing import final
from plover.steno import Stroke

from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.declare_banks import declare_banks
from plover_hatchery.lib.pipes.join import tuplify
from plover_hatchery.lib.pipes.lookup_result_filter import lookup_result_filter
from plover_hatchery.lib.trie import Trie, TransitionKey
from plover_hatchery.lib.trie.LookupResult import LookupResult
from plover_hatchery.lib.trie.NondeterministicTrie import NondeterministicTrie

from ..trie import TransitionCostInfo
from ..config import TRIE_STROKE_BOUNDARY_KEY, TRIE_LINKER_KEY

from .Plugin import GetPluginApi, Plugin, define_plugin
from .banks import banks, BanksState


def linker_chord(
    chord: str,
    *,
    stroke_must_have_linker: Callable[[Stroke], bool]=lambda stroke: False,
    stroke_must_not_have_linker: Callable[[Stroke], bool]=lambda stroke: False,
) -> Plugin[None]:
    linker_stroke = Stroke.from_steno(chord)

    @define_plugin(linker_chord)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_info = get_plugin_api(declare_banks)
        banks_hooks = get_plugin_api(banks)
        filtering_api = get_plugin_api(lookup_result_filter)

        @dataclass
        @final
        class LinkerChordState:
            newest_post_linker_node: int | None = None

        
        @banks_hooks.begin.listen(linker_chord)
        def _(**_):
            return LinkerChordState()


        @banks_hooks.before_complete_consonant.listen(linker_chord)
        def _(banks_state: BanksState, state: LinkerChordState, left_node: int | None", right_node: "int | None, **_):
            if right_node is None: return

            new_stroke_node = banks_state.trie.follow(right_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, banks_state.entry_id)).dst_node_id
            post_linker_node = banks_state.trie.follow_chain(new_stroke_node, linker_stroke.keys(), TransitionCostInfo(0, banks_state.entry_id)).dst_node_id
            
            if left_node is not None:
                _ = banks_state.trie.link(post_linker_node, left_node, None, TransitionCostInfo(0, banks_state.entry_id))

            
            state.newest_post_linker_node = post_linker_node


        @banks_hooks.complete_consonant.listen(linker_chord)
        def _(banks_state: BanksState, state: LinkerChordState, **_):
            banks_state.left_srcs += tuplify(state.newest_post_linker_node)
            banks_state.mid_srcs += tuplify(state.newest_post_linker_node)

            banks_state.last_left_nodes += tuplify(state.newest_post_linker_node)


            state.newest_post_linker_node = None


        @banks_hooks.before_complete_vowel.listen(linker_chord)
        def _(banks_state: BanksState, state: LinkerChordState, mid_node: int | None, **_):
            if mid_node is None: return

            new_stroke_node = banks_state.trie.follow(mid_node, TRIE_STROKE_BOUNDARY_KEY, TransitionCostInfo(0, banks_state.entry_id)).dst_node_id
            post_linker_node = banks_state.trie.follow_chain(new_stroke_node, linker_stroke.keys(), TransitionCostInfo(0, banks_state.entry_id)).dst_node_id

            
            state.newest_post_linker_node = post_linker_node


        @banks_hooks.complete_vowel.listen(linker_chord)
        def _(banks_state: BanksState, state: LinkerChordState, **_):
            banks_state.left_srcs += tuplify(state.newest_post_linker_node)
            banks_state.mid_srcs += tuplify(state.newest_post_linker_node)


            state.newest_post_linker_node = None


        @filtering_api.check_should_keep.listen(linker_chord)
        def _(outline: tuple[Stroke, ...], **_):
            for i, stroke in enumerate(outline):
                if i == 0: continue

                stroke -= banks_info.positionless


                has_linker = stroke_starts_with(stroke, linker_stroke)

                if has_linker and stroke_must_not_have_linker(stroke - linker_stroke):
                    return False
                
                if not has_linker and stroke_must_have_linker(stroke):
                    return False

            
            return True


        def stroke_starts_with(stroke: Stroke, substroke: Stroke):
            return all(key1 == key2 for key1, key2 in zip(stroke, substroke))


    return plugin