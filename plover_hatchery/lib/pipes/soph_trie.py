

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Iterable, NamedTuple, Protocol, final

from plover.steno import Stroke

from plover_hatchery.lib.pipes.Hook import Hook
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.floating_keys import floating_keys
from plover_hatchery.lib.sopheme import SophemeSeq, SophemeSeqPhoneme
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie, NodeSrc, Trie, TriePath
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.types import Soph, EntryIndex



@dataclass(frozen=True)
class SophChordAssociation:
    soph: Soph
    chord: Stroke

@final
@dataclass
class SophTrieApi:
    class ValidateOutline(Protocol):
        def __call__(self, *, outline: tuple[Stroke, ...]) -> bool: ...
    class ProcessOutline(Protocol):
        def __call__(self, *, outline: tuple[Stroke, ...]) -> tuple[Stroke, ...]: ...
    class ValidateLookupResult(Protocol):
        def __call__(
            self,
            *,
            lookup_result: LookupResult[EntryIndex],
            trie: NondeterministicTrie[Soph, EntryIndex],
            outline: tuple[Stroke, ...],
            sophs_and_chords_used: tuple[SophChordAssociation, ...],
        ) -> bool: ...
            

    trie: NondeterministicTrie[Soph, EntryIndex]

    validate_outline = Hook(ValidateOutline)
    process_outline = Hook(ProcessOutline)
    validate_lookup_result = Hook(ValidateLookupResult)


def soph_trie(map_phoneme_to_soph: Callable[[SophemeSeqPhoneme], Iterable[Soph]], sophs_to_chords_dict: dict[str, str]) -> Plugin[SophTrieApi]:
    @define_plugin(soph_trie)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_):
        floating_keys_api = get_plugin_api(floating_keys)


        trie: NondeterministicTrie[Soph, EntryIndex] = NondeterministicTrie()

        api = SophTrieApi(trie)



        ### Lookup building #############################################################
        # We construct a nondeterministic trie whose transitions are sophs, gathered from an entry's phonemes.
        # The translations are the translations of each sopheme sequence.

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



        ### Chord -> soph mapping ######################################################
        # We build a trie whose transitions are keys in strokes, so we can lookup the different possible Sophs each
        # chord could map to. We also track the required floaters in the chord so we can check if a user's stroke
        # contains them before allowing a soph to be used, should its chord have a floater (e.g., *T for th).


        class ChordToSophSearcher:
            def __init__(self, sophs_to_chords_dict: dict[str, str]):
                self.__chords_to_sophs: Trie[str, list[ChordToSophSearcher.Result]] = Trie()

                for soph_value, chords_steno in sophs_to_chords_dict.items():
                    soph = Soph(soph_value)
                    for chord_steno in chords_steno.split():
                        chord_rest, chord_floaters = floating_keys_api.split(Stroke.from_steno(chord_steno))
                        result = ChordToSophSearcher.Result(soph, chord_floaters)


                        dst_node = self.__chords_to_sophs.follow_chain(self.__chords_to_sophs.ROOT, chord_rest.keys())
                        sophs = self.__chords_to_sophs.get_translation(dst_node)
                        if sophs is None:
                            self.__chords_to_sophs.set_translation(dst_node, [result])
                        else:
                            sophs.append(result)


            @dataclass(frozen=True)
            class Result:
                soph: Soph
                required_floaters: Stroke


            def begin_search(self):
                return ChordToSophSearcher.Session(self)


            @property
            def chords_to_sophs(self):
                return self.__chords_to_sophs


            class Session:
                class Item(NamedTuple):
                    soph_reult: "ChordToSophSearcher.Result"
                    chord_starting_key_index: int


                def __init__(self, chord_finder: "ChordToSophSearcher"):
                    self.__chord_finder = chord_finder
                    self.__node_data_for_chords_to_sophs_lookup: list[ChordToSophSearchNode] = [ChordToSophSearchNode(chord_finder.chords_to_sophs.ROOT, 0)]
                    self.__current_key_index = 0


                def possible_sophs_after_consuming(self, key: str):
                    # Continue the ongoing trie traversals
                    new_node_indices: list[ChordToSophSearchNode] = []
                    for trie_node in self.__node_data_for_chords_to_sophs_lookup:
                        dst_node = self.__chord_finder.chords_to_sophs.traverse(trie_node.trie_node, key)
                        if dst_node is None: continue

                        new_node_indices.append(ChordToSophSearchNode(dst_node, trie_node.chord_starting_key_index))

                        soph_results = self.__chord_finder.chords_to_sophs.get_translation(dst_node)

                        if soph_results is None: continue


                        for soph_result in soph_results:
                            yield ChordToSophSearcher.Session.Item(soph_result, trie_node.chord_starting_key_index)


                    # Add a root node so the next key triggers a new traversal starting from the root
                    new_node_indices.append(ChordToSophSearchNode(chord_finder.chords_to_sophs.ROOT, self.__current_key_index + 1))


                    self.__node_data_for_chords_to_sophs_lookup = new_node_indices
                    self.__current_key_index += 1

                
                def finish_stroke(self):
                    # We don't want chords to bleed across strokes, so reset them
                    self.__node_data_for_chords_to_sophs_lookup = [ChordToSophSearchNode(self.__chord_finder.chords_to_sophs.ROOT, self.__current_key_index)]


        chord_finder = ChordToSophSearcher(sophs_to_chords_dict)


        ### Lookup ######################################################################
        # We go key by key in the user's outline. For each key, check all possible configurations of sophs that the
        # outline could represent, traversing the nondeterministic soph trie as soon as sophs are found.
        # After consuming all the keys, find the translation with the lowest cost.

        @dataclass(frozen=True)
        class ChordToSophSearchNode:
            trie_node: int
            chord_starting_key_index: int

            
                
        @dataclass(frozen=True)
        class SophChordAssociationWithUnresolvedChord:
            soph: Soph
            chord_start_key_index: int
            required_floaters: Stroke


        @dataclass(frozen=True)
        class SophLookupPath:


            trie_path: TriePath = TriePath(0, ())
            sophs_and_chords_used: tuple[SophChordAssociationWithUnresolvedChord, ...] = ()

        class SophPathFinder:
            """Manages the key-by-key iteration phase of lookup."""


            def __init__(self):
                self.__possible_soph_paths: list[list[SophLookupPath]] = [[SophLookupPath()]]
                self.__chord_search = chord_finder.begin_search()
                self.__consumed_keys: list[str] = []

            def __consume_key(self, key: str, stroke: Stroke):
                new_possible_sophs: list[SophLookupPath] = []

                for soph_result, chord_start_key_index in self.__chord_search.possible_sophs_after_consuming(key):
                    if soph_result.required_floaters not in stroke: continue

                    for path in self.__possible_soph_paths[chord_start_key_index]:
                        new_possible_sophs.extend(
                            SophLookupPath(
                                new_trie_path,
                                path.sophs_and_chords_used + (SophChordAssociationWithUnresolvedChord(soph_result.soph, chord_start_key_index, soph_result.required_floaters),)
                            )
                            for new_trie_path in trie.traverse((path.trie_path,), soph_result.soph)
                        )

                self.__possible_soph_paths.append(new_possible_sophs)
                self.__consumed_keys.append(key)
            

            def __finish_stroke(self):
                self.__chord_search.finish_stroke()


            def __get_final_paths(self):
                return self.__possible_soph_paths[-1]


            @staticmethod
            def get_paths_from_outline(outline: tuple[Stroke, ...]):
                soph_path_finder = SophPathFinder()
                consumed_keys: list[str] = []

                for stroke_index, stroke in enumerate(outline):
                    if stroke_index > 0:
                        soph_path_finder.__finish_stroke()

                    for key in stroke - floating_keys_api.floaters:
                        soph_path_finder.__consume_key(key, stroke)
                        consumed_keys.append(key)

                return soph_path_finder.__get_final_paths(), consumed_keys


        class LookupRunner:
            """Manages lookup results after they have been found by a lookup session."""


            class LookupResultWithAssociations(NamedTuple):
                lookup_result: LookupResult[EntryIndex]
                sophs_and_chords_used: tuple[SophChordAssociation, ...]


            @staticmethod
            def __resolve_soph_chord_associations(associations: tuple[SophChordAssociationWithUnresolvedChord, ...], outline_keys: list[str]):
                for i, association in enumerate(associations):
                    if i < len(associations) - 1:
                        next_association = associations[i + 1]
                        yield SophChordAssociation(
                            association.soph,
                            Stroke.from_steno(outline_keys[association.chord_start_key_index:next_association.chord_start_key_index]) + association.required_floaters
                        )

                    else:
                        yield SophChordAssociation(
                            association.soph,
                            Stroke.from_steno(outline_keys[association.chord_start_key_index:]) + association.required_floaters
                        )


            @staticmethod
            def __items_from_soph_path_result(final_path: SophLookupPath, consumed_keys: list[str]):
                for lookup_result in trie.get_translations_and_costs((final_path.trie_path,)):
                    yield lookup_result, LookupRunner.__resolve_soph_chord_associations(final_path.sophs_and_chords_used, consumed_keys)


            @staticmethod
            def get_processed_lookup_results(outline: tuple[Stroke, ...]):
                final_paths, consumed_keys = SophPathFinder.get_paths_from_outline(outline)
                for final_path in final_paths:
                    yield from LookupRunner.__items_from_soph_path_result(final_path, consumed_keys)
                    




        class MinTranslationBuilder:
            def __init__(self):
                self.__min_costs: dict[EntryIndex, float] = defaultdict(lambda: float("inf"))
                self.__min_cost_results: dict[EntryIndex, LookupResult[EntryIndex]] = {}


            def __record_lookup_result_if_has_min_cost(self, lookup_result: LookupResult[EntryIndex], sophs_and_chords_used: Iterable[SophChordAssociation], outline_for_filtering: tuple[Stroke, ...]):
                if lookup_result.cost >= self.__min_costs[lookup_result.translation]: return

                if not all(
                    handler(lookup_result=lookup_result, trie=trie, outline=outline_for_filtering, sophs_and_chords_used=tuple(sophs_and_chords_used))
                    for handler in api.validate_lookup_result.handlers()
                ):
                    return

                self.__min_costs[lookup_result.translation] = lookup_result.cost
                self.__min_cost_results[lookup_result.translation] = lookup_result


            def __get_sorted_min_translations(self):
                return sorted(self.__min_cost_results.values(), key=lambda result: result.cost)


            @staticmethod
            def build(outline: tuple[Stroke, ...], outline_for_filtering: tuple[Stroke, ...]):
                builder = MinTranslationBuilder()
                for lookup_result, sophs_and_chords_used in LookupRunner.get_processed_lookup_results(outline):
                    builder.__record_lookup_result_if_has_min_cost(lookup_result, sophs_and_chords_used, outline_for_filtering)
                
                return builder.__get_sorted_min_translations()




        def nth_variation(choices: list[LookupResult[EntryIndex]], n_variation: int, translations: list[str]):
            # index = n_variation % (len(choices) + 1)
            # return choices[index][0] if index != len(choices) else None
            return translations[choices[n_variation % len(choices)].translation.value]
        

        @base_hooks.lookup.listen(soph_trie)
        def _(stroke_stenos: tuple[str, ...], translations: list[str], **_) -> "str | None":
            outline = tuple(Stroke.from_steno(steno) for steno in stroke_stenos)
            if len(outline[-1]) == 0: return None # TODO

            if not all(
                handler(outline=outline)
                for handler in api.validate_outline.handlers()
            ):
                return None

            for handler in api.process_outline.handlers():
                outline = handler(outline=outline)
            
            
            translation_choices = MinTranslationBuilder().build(outline, outline)
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

        return api

    return plugin