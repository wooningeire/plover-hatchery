from collections import defaultdict
from plover_hatchery.lib.config import TRIE_STROKE_BOUNDARY_KEY
from plover_hatchery.lib.pipes.Plugin import Plugin


from typing import Any, Callable, Generator, Protocol, final
from dataclasses import dataclass

from plover.steno import Stroke

from plover_hatchery.lib.pipes.declare_banks import declare_banks
from plover_hatchery.lib.pipes.key_by_key_lookup import key_by_key_lookup
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie, Trie, TriePath
from plover_hatchery.lib.trie.Transition import TransitionKey

from ..sopheme import Sound
from .banks import banks, BanksState
from .join import NodeSrc, join_on_strokes, link_join_on_strokes, tuplify
from .Plugin import define_plugin, GetPluginApi
from .Hook import Hook


@final
@dataclass
class LeftAltChordsState:
    newest_left_alt_node: "int | None" = None
    last_left_alt_nodes: tuple[NodeSrc, ...] = ()
    """Collection of left alt nodes since which only vowels, optional sounds, or silent sounds have occurred."""


def left_alt_chords(chords: Callable[[Sound], Generator[Stroke, None, None]]) -> Plugin[None]:
    """Adds support for alternate chords, or chords that are only available when the typical "main" chord cannot be used.
    
    Example: KOFT ↦ cost. -F is an alt chord for S. It is available because the main chord -S could not be used in this stroke, since it comes after -T.
    """


    @define_plugin(left_alt_chords)
    def plugin(get_plugin_api: GetPluginApi, **_):
        banks_api = get_plugin_api(banks)
        banks_info = get_plugin_api(declare_banks)
        key_by_key_lookup_api = get_plugin_api(key_by_key_lookup)


        @final
        @dataclass
        class AttemptedAltChordPathData:
            """Data for a path in the lookup trie corresponding with an alt chord, used during result validation"""

            consonant: Sound
            attempted_alt_chord: Stroke

        transitions_tries: dict[int, Trie[TransitionKey, AttemptedAltChordPathData]] = defaultdict(Trie)


        @banks_api.begin.listen(left_alt_chords)
        def _():
            return LeftAltChordsState()
        

        @banks_api.before_complete_consonant.listen(left_alt_chords)
        def _(state: LeftAltChordsState, banks_state: BanksState, left_node: "int | None", consonant: Sound, **_):
            left_alt_paths = link_join_on_strokes(
                banks_state.trie,
                NodeSrc.increment_costs(banks_state.left_srcs, 3),
                left_node,
                chords(consonant),
                banks_state.entry_id,
            )


            for transition_seq in left_alt_paths.transition_seqs:
                # Store this group of transitions so we can validate using it later
                transitions_trie = transitions_tries[banks_state.entry_id]

                exit_node = transitions_trie.follow_chain(transitions_trie.ROOT, transition_seq.transitions)
                transitions_trie.set_translation(exit_node, AttemptedAltChordPathData(consonant, transition_seq.chord))


            state.newest_left_alt_node = left_alt_paths.dst_node_id

        
        @banks_api.complete_consonant.listen(left_alt_chords)
        def _(state: LeftAltChordsState, banks_state: BanksState, **_):
            new_last_left_alt_nodes = tuplify(state.newest_left_alt_node)

            banks_state.left_srcs += new_last_left_alt_nodes


        @dataclass
        class FoundPath:
            dst_node: int
            transition_indices: tuple[int, ...]


        @key_by_key_lookup_api.validate_path.listen(left_alt_chords)
        def _(lookup_result: LookupResult[int], trie: NondeterministicTrie[str, int], **_):
            # Return true if, for every alt chord path taken, any of the main chords

            for found_path, path_data in taken_alt_chord_paths(lookup_result):
                preceding_chord = get_adjacent_chord(found_path, lookup_result, trie, True)
                following_chord = get_adjacent_chord(found_path, lookup_result, trie, False)

                could_have_used_main_chord = True

                for main_chord in banks_api.left_chords(path_data.consonant):
                    if not banks_info.can_add_stroke_on(preceding_chord, main_chord):
                        could_have_used_main_chord = False
                        break
                    
                    if not banks_info.can_add_stroke_on(main_chord, following_chord):
                        could_have_used_main_chord = False
                        break
                
                if could_have_used_main_chord:
                    return False

            return True


        def get_adjacent_chord(path: FoundPath, lookup_result: LookupResult[int], trie: NondeterministicTrie[str, int], lookbehind: bool):
            edge_transition_index = path.transition_indices[0] if lookbehind else path.transition_indices[-1]

            if lookbehind and edge_transition_index == 0:
                return Stroke.from_integer(0)
            
            if not lookbehind and edge_transition_index == len(lookup_result.transitions) - 1:
                return Stroke.from_integer(0)


            transition_index = edge_transition_index
            adjacent_key_id = None
            while adjacent_key_id is None:
                if lookbehind:
                    transition_index -= 1
                else:
                    transition_index += 1

                adjacent_key_id = lookup_result.transitions[transition_index].key_id

            adjacent_key = trie.get_key(adjacent_key_id)

            if adjacent_key == TRIE_STROKE_BOUNDARY_KEY:
                return Stroke.from_integer(0)


            return Stroke.from_steno(adjacent_key)



        def taken_alt_chord_paths(lookup_result: LookupResult[int]):
            entry_id = lookup_result.translation
            if entry_id not in transitions_tries:
                return


            transitions_trie = transitions_tries[entry_id]

            found_paths: list[FoundPath] = []
            for transition_index, transition in enumerate(lookup_result.transitions):
                found_paths.append(FoundPath(transitions_trie.ROOT, ()))

                for found_node in found_paths:
                    dst_node = transitions_trie.traverse(found_node.dst_node, transition)
                    if dst_node is None:
                        continue

                    found_path = FoundPath(dst_node, found_node.transition_indices + (transition_index,))
                    found_paths.append(found_path)

                    path_data = transitions_trie.get_translation(dst_node)
                    if path_data is None:
                        continue

                    yield found_path, path_data


        return None


    return plugin