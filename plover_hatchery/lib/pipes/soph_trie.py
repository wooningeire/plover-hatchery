

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Iterable, final

from plover.steno import Stroke

from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.floating_keys import floating_keys
from plover_hatchery.lib.sopheme import SophemeSeq, SophemeSeqPhoneme
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie, NodeSrc, Trie, TriePath
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.types import Soph, EntryIndex



@final
@dataclass(frozen=True)
class SophBasedTrieConstructionApi:
    trie: NondeterministicTrie[Soph, EntryIndex]

def soph_trie(map_phoneme_to_soph: Callable[[SophemeSeqPhoneme], Iterable[Soph]], sophs_to_chords_dict: dict[str, str]) -> Plugin[SophBasedTrieConstructionApi]:
    @define_plugin(soph_trie)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_):
        floating_keys_api = get_plugin_api(floating_keys)


        trie: NondeterministicTrie[Soph, EntryIndex] = NondeterministicTrie()

        api = SophBasedTrieConstructionApi(trie)


        @base_hooks.add_entry.listen(soph_trie)
        def _(sophemes: SophemeSeq, entry_id: EntryIndex, **_):
            src_nodes: list[NodeSrc] = [NodeSrc(0)]
            new_src_nodes: list[NodeSrc] = []


            for phoneme in sophemes.phonemes():
                sophs = map_phoneme_to_soph(phoneme)

                paths = trie.join(src_nodes, sophs, entry_id)
                if paths.dst_node_id is not None:
                    new_src_nodes.append(NodeSrc(paths.dst_node_id))


                src_nodes = new_src_nodes
                if not phoneme.keysymbol.optional:
                    new_src_nodes = []


            for src in src_nodes:
                trie.set_translation(src.node, entry_id)


        @dataclass(frozen=True)
        class SophResult:
            soph: Soph
            required_floaters: Stroke


        chords_to_sophs: Trie[str, list[SophResult]] = Trie()
        for soph_value, chords_steno in sophs_to_chords_dict.items():
            soph = Soph(soph_value)
            for chord_steno in chords_steno.split():
                chord_rest, chord_floaters = floating_keys_api.split(Stroke.from_steno(chord_steno))
                result = SophResult(soph, chord_floaters)


                dst_node = chords_to_sophs.follow_chain(chords_to_sophs.ROOT, chord_rest.keys())
                sophs = chords_to_sophs.get_translation(dst_node)
                if sophs is None:
                    chords_to_sophs.set_translation(dst_node, [result])
                else:
                    sophs.append(result)


        @dataclass(frozen=True)
        class OngoingTrieNode:
            trie_node: int
            src_key_index: int

        class LookupState:
            def __init__(self):
                self.__possible_soph_paths: list[list[TriePath]] = [[TriePath(0, ())]]
                self.__chords_to_sophs_node_indices: list[OngoingTrieNode] = [OngoingTrieNode(chords_to_sophs.ROOT, 0)]
                self.__key_index = 0

            def consume_key(self, key: str, stroke: Stroke):
                floaters = stroke & floating_keys_api.floaters


                # Continue the ongoing trie traversals
                new_node_indices: list[OngoingTrieNode] = []
                new_possible_sophs: list[TriePath] = []
                for trie_node in self.__chords_to_sophs_node_indices:
                    dst_node = chords_to_sophs.traverse(trie_node.trie_node, key)
                    if dst_node is None: continue

                    new_node_indices.append(OngoingTrieNode(dst_node, trie_node.src_key_index))


                    soph_results = chords_to_sophs.get_translation(dst_node)

                    if soph_results is None: continue


                    for result in soph_results:
                        if result.required_floaters not in stroke: continue
                        new_possible_sophs.extend(trie.traverse(self.__possible_soph_paths[trie_node.src_key_index], result.soph))


                # Add a root node so the next key triggers a new traversal starting from the root
                new_node_indices.append(OngoingTrieNode(chords_to_sophs.ROOT, self.__key_index + 1))


                self.__possible_soph_paths.append(new_possible_sophs)
                self.__chords_to_sophs_node_indices = new_node_indices
                self.__key_index += 1

            
            def finish_stroke(self):
                # We don't want traversals to bleed across strokes, so reset them
                self.__chords_to_sophs_node_indices = [OngoingTrieNode(chords_to_sophs.ROOT, self.__key_index)]

            
            def get_lookup_results(self):
                return trie.get_translations_and_costs(self.__possible_soph_paths[-1])

            
        class LookupRunner:
            def __init__(self, stroke_stenos: tuple[str, ...]):
                self.__outline = tuple(Stroke.from_steno(steno) for steno in stroke_stenos)
                self.__filtering_end_index = len(self.__outline)


            def __run_lookup(self):
                state = LookupState()

                for stroke_index, stroke in enumerate(self.__outline):
                    if stroke_index > 0:
                        state.finish_stroke()

                    for key in stroke - floating_keys_api.floaters:
                        state.consume_key(key, stroke)

                return state.get_lookup_results()


            def get_translation_choices(self):
                min_costs: dict[EntryIndex, float] = defaultdict(lambda: float("inf"))
                min_cost_results: dict[EntryIndex, LookupResult[EntryIndex]] = {}

                outline_for_filtering = self.__outline[:self.__filtering_end_index]
                for lookup_result in self.__run_lookup():
                    if lookup_result.cost >= min_costs[lookup_result.translation]: continue
                    # if not filtering_api.should_keep(lookup_result, trie, outline_for_filtering):
                    #     continue

                    min_costs[lookup_result.translation] = lookup_result.cost
                    min_cost_results[lookup_result.translation] = lookup_result

                return sorted(min_cost_results.values(), key=lambda result: result.cost)



        def nth_variation(choices: list[LookupResult[EntryIndex]], n_variation: int, translations: list[str]):
            # index = n_variation % (len(choices) + 1)
            # return choices[index][0] if index != len(choices) else None
            return translations[choices[n_variation % len(choices)].translation.value]
        

        @base_hooks.lookup.listen(soph_trie)
        def _(stroke_stenos: tuple[str, ...], translations: list[str], **_) -> "str | None":
            
            
            translation_choices = LookupRunner(stroke_stenos).get_translation_choices()
            n_variation = 0

            # if debug:
            #     return _join_all_translations(trie, translation_choices, translations)
            
            if len(translation_choices) == 0: return None

            return nth_variation(translation_choices, n_variation, translations)
            # if len(positionless) == 0:
            #     return nth_variation(translation_choices, n_variation, translations)
            # else:
            #     for transition in reversed(first_choice.transitions):
            #         if trie.transition_has_key(transition, TRIE_STROKE_BOUNDARY_KEY): break
            #         if not trie.transition_has_key(transition, banks_info.positionless.rtfcre): continue

            #         return nth_variation(translation_choices, n_variation, translations)

            # return nth_variation(translation_choices, n_variation + 1, translations) if len(translation_choices) > 1 else None

            # return ",".join()

        return api

    return plugin