

from cgitb import lookup
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Iterable, NamedTuple, Protocol, final

from plover.steno import Stroke

from plover_hatchery.lib.pipes.Hook import Hook
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.floating_keys import floating_keys
from plover_hatchery.lib.pipes.plugin_utils import join_sophs_to_chords_dicts
from plover_hatchery.lib.sopheme import SophemeSeq, SophemeSeqPhoneme
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie, NodeSrc, Trie, TriePath, JoinedTriePaths, TransitionCostKey, TransitionKey
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.types import Soph, EntryIndex



class SophChordAssociation(NamedTuple):
    sophs: tuple[Soph, ...]
    chord: Stroke
    chord_starts_new_stroke: bool
    phonemes: tuple[SophemeSeqPhoneme, ...]
    transitions: tuple[TransitionKey, ...]

class LookupResultWithAssociations(NamedTuple):
    lookup_result: LookupResult[EntryIndex]
    sophs_and_chords_used: tuple[SophChordAssociation, ...]

@final
@dataclass
class SophTrieApi:
    class BeginAddEntry(Protocol):
        def __call__(self, *, trie: NondeterministicTrie[Soph, EntryIndex], sophemes: SophemeSeq, entry_id: EntryIndex) -> Any: ...
    class AddSophTransition(Protocol):
        def __call__(
            self,
            *,
            state: Any,
            phoneme: SophemeSeqPhoneme,
            sophs: set[Soph],
            paths: JoinedTriePaths,
            node_srcs: tuple[NodeSrc, ...],
            new_node_srcs: list[NodeSrc],
            trie: NondeterministicTrie[Soph, EntryIndex],
            entry_id: EntryIndex,
        ): ...
    class BeginLookup(Protocol):
        def __call__(self, *, outline: tuple[Stroke, ...]) -> Any: ...
    class ProcessOutline(Protocol):
        def __call__(self, *, state: Any, outline: tuple[Stroke, ...]) -> "tuple[Stroke, ...] | None": ...
    class ValidateLookupResult(Protocol):
        def __call__(
            self,
            *,
            state: Any,
            result: LookupResultWithAssociations,
            trie: NondeterministicTrie[Soph, EntryIndex],
            original_outline: tuple[Stroke, ...],
            outline: tuple[Stroke, ...],
        ) -> bool: ...
    class SelectTranslation(Protocol):
        def __call__(
            self,
            *,
            state: Any,
            trie: NondeterministicTrie[Soph, EntryIndex],
            choices: list[LookupResultWithAssociations],
            translations: list[str],
            original_outline: tuple[Stroke, ...],
            outline: tuple[Stroke, ...],
        ) -> "str | None": ...
            

    trie: NondeterministicTrie[Soph, EntryIndex]
    transition_data: dict[TransitionCostKey, SophemeSeqPhoneme]

    def register_transition(self, transition: TransitionKey, entry_id: EntryIndex, phoneme: SophemeSeqPhoneme):
        cost_key = TransitionCostKey(transition, entry_id.value)
        self.transition_data[cost_key] = phoneme


    begin_add_entry = Hook(BeginAddEntry)
    add_soph_transition = Hook(AddSophTransition)
    begin_lookup = Hook(BeginLookup)
    process_outline = Hook(ProcessOutline)
    validate_lookup_result = Hook(ValidateLookupResult)
    select_translation = Hook(SelectTranslation)


def soph_trie(
    *,
    map_phoneme_to_sophs: Callable[[SophemeSeqPhoneme], Iterable[str]],
    sophs_to_chords_dicts: Iterable[dict[str, str]],
    vowel_sophs_str: str,
) -> Plugin[SophTrieApi]:
    sophs_to_chords = join_sophs_to_chords_dicts(sophs_to_chords_dicts)


    @define_plugin(soph_trie)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_):
        floating_keys_api = get_plugin_api(floating_keys)


        vowel_sophs: set[Soph] = {Soph(value) for value in vowel_sophs_str.split()}

        trie: NondeterministicTrie[Soph, EntryIndex] = NondeterministicTrie()
        transition_phonemes: dict[TransitionCostKey, SophemeSeqPhoneme] = {}

        api = SophTrieApi(trie, transition_phonemes)



        ### Lookup building #############################################################
        # We construct a nondeterministic trie whose transitions are sophs, gathered from an entry's phonemes.
        # The translations are the translations of each sopheme sequence.

        @base_hooks.add_entry.listen(soph_trie)
        def _(sophemes: SophemeSeq, entry_id: EntryIndex, **_):
            states = api.begin_add_entry.emit_and_store_outputs(trie=trie, sophemes=sophemes, entry_id=entry_id)


            src_nodes: list[NodeSrc] = [NodeSrc(0)]
            new_src_nodes: list[NodeSrc] = []


            for phoneme in sophemes.phonemes():
                if not phoneme.keysymbol.optional:
                    new_src_nodes = []
                else:
                    new_src_nodes = list(NodeSrc.increment_costs(new_src_nodes, 5))


                sophs = set(Soph(value) for value in map_phoneme_to_sophs(phoneme))
                if any(soph in vowel_sophs for soph in sophs):
                    sophs.add(Soph("@"))


                paths = trie.join(src_nodes, sophs, entry_id)
                if paths.dst_node_id is not None:
                    new_src_nodes.append(NodeSrc(paths.dst_node_id))

                for seq in paths.transition_seqs:
                    api.register_transition(seq.transitions[0], entry_id, phoneme)


                api.add_soph_transition.emit_with_states(
                    states,
                    phoneme=phoneme,
                    sophs=sophs,
                    paths=paths,
                    node_srcs=tuple(src_nodes),
                    new_node_srcs=new_src_nodes,
                    trie=trie,
                    entry_id=entry_id,
                )


                src_nodes = new_src_nodes


            for src in src_nodes:
                trie.set_translation(src.node, entry_id)


        # @base_hooks.complete_build_lookup.listen(soph_trie)
        # def _(**_):
        #     print(trie)



        ### Chord -> soph mapping ######################################################
        # We build a trie whose transitions are keys in strokes, so we can lookup the different possible Sophs each
        # chord could map to. We also track the required floaters in the chord so we can check if a user's stroke
        # contains them before allowing a soph to be used, should its chord have a floater (e.g., *T for th).


        class ChordToSophSearcher:
            def __init__(self, sophs_to_chords_dicts: Iterable[dict[str, str]]):
                self.__chords_to_sophs: Trie[str, list[ChordToSophSearcher.Result]] = Trie()

                for sophs, chords in sophs_to_chords.items():
                    for chord in chords:
                        chord_rest, chord_floaters = floating_keys_api.split(chord)
                        result = ChordToSophSearcher.Result(sophs, chord)


                        dst_node = self.__chords_to_sophs.follow_chain(self.__chords_to_sophs.ROOT, chord_rest.keys())
                        existing_soph_seqs = self.__chords_to_sophs.get_translation(dst_node)
                        if existing_soph_seqs is None:
                            self.__chords_to_sophs.set_translation(dst_node, [result])
                        else:
                            existing_soph_seqs.append(result)


            @dataclass(frozen=True)
            class Result:
                sophs: tuple[Soph, ...]
                chord: Stroke

                @property
                def required_floaters(self):
                    return floating_keys_api.only_floaters(self.chord)


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


        chord_finder = ChordToSophSearcher(sophs_to_chords_dicts)


        ### Lookup ######################################################################
        # We go key by key in the user's outline. For each key, check all possible configurations of sophs that the
        # outline could represent, traversing the nondeterministic soph trie as soon as sophs are found.
        # After consuming all the keys, find the translation with the lowest cost.

        @dataclass(frozen=True)
        class ChordToSophSearchNode:
            trie_node: int
            chord_starting_key_index: int


        class SophChordAssociationWithUnresolvedPhonemes(NamedTuple):
            sophs: tuple[Soph, ...]
            chord: Stroke
            chord_starts_new_stroke: bool
            transitions: tuple[TransitionKey, ...]


        @dataclass(frozen=True)
        class SophLookupPath:
            trie_path: TriePath = TriePath(0, ())
            sophs_and_chords_used: tuple[SophChordAssociationWithUnresolvedPhonemes, ...] = ()


        class SophPathFinder:
            """Manages the key-by-key iteration phase of lookup."""


            def __init__(self):
                self.__possible_soph_paths: list[list[SophLookupPath]] = [[SophLookupPath()]]
                self.__chord_search = chord_finder.begin_search()
                self.__consumed_keys: list[str] = []
                self.__is_new_stroke = True

            def __consume_key(self, key: str, stroke: Stroke):
                new_possible_sophs: list[SophLookupPath] = []

                for soph_result, chord_start_key_index in self.__chord_search.possible_sophs_after_consuming(key):
                    if soph_result.required_floaters not in stroke: continue

                    for path in self.__possible_soph_paths[chord_start_key_index]:
                        new_possible_sophs.extend(
                            SophLookupPath(
                                new_trie_path,
                                path.sophs_and_chords_used + (
                                    SophChordAssociationWithUnresolvedPhonemes(
                                        soph_result.sophs,
                                        soph_result.chord,
                                        self.__is_new_stroke,
                                        new_trie_path.transitions[len(path.trie_path.transitions):]
                                    ),
                                )
                            )
                            for new_trie_path in trie.traverse_chain((path.trie_path,), soph_result.sophs)
                        )

                self.__possible_soph_paths.append(new_possible_sophs)
                self.__consumed_keys.append(key)
                self.__is_new_stroke = False
            

            def __finish_stroke(self):
                self.__chord_search.finish_stroke()
                self.__is_new_stroke = True


            def __get_final_paths(self):
                return self.__possible_soph_paths[-1]


            @staticmethod
            def get_paths_from_outline(outline: tuple[Stroke, ...]):
                soph_path_finder = SophPathFinder()

                for stroke_index, stroke in enumerate(outline):
                    if stroke_index > 0:
                        soph_path_finder.__finish_stroke()

                    for key in stroke - floating_keys_api.floaters:
                        soph_path_finder.__consume_key(key, stroke)

                return soph_path_finder.__get_final_paths()


        class LookupRunner:
            """Manages lookup results after they have been found by a lookup session."""


            @staticmethod
            def __resolve_phonemes(lookup_result: LookupResult[EntryIndex], association: SophChordAssociationWithUnresolvedPhonemes):
                phonemes: list[SophemeSeqPhoneme] = []
                for transition in association.transitions:
                    cost_key = TransitionCostKey(transition, lookup_result.translation_id)
                    if cost_key not in transition_phonemes: continue

                    phonemes.append(transition_phonemes[cost_key])
                
                return tuple(phonemes)


            @staticmethod
            def __items_from_soph_path_result(final_path: SophLookupPath):
                for lookup_result in trie.get_translations_and_costs((final_path.trie_path,)):
                    new_associations = tuple(
                        SophChordAssociation(
                            association.sophs,
                            association.chord,
                            association.chord_starts_new_stroke,
                            LookupRunner.__resolve_phonemes(lookup_result, association),
                            association.transitions,
                        )
                        for association in final_path.sophs_and_chords_used
                    )

                    yield lookup_result, new_associations


            @staticmethod
            def get_processed_lookup_results(outline: tuple[Stroke, ...]):
                for final_path in SophPathFinder.get_paths_from_outline(outline):
                    yield from LookupRunner.__items_from_soph_path_result(final_path)
                    




        class MinTranslationBuilder:
            def __init__(self):
                self.__min_costs: dict[EntryIndex, float] = defaultdict(lambda: float("inf"))
                self.__min_cost_results: dict[EntryIndex, LookupResultWithAssociations] = {}


            def __record_lookup_result_if_has_min_cost(
                self,
                lookup_result: LookupResult[EntryIndex],
                sophs_and_chords_used: Iterable[SophChordAssociation],
                outline: tuple[Stroke, ...],
                original_outline: tuple[Stroke, ...],
                states: dict[int, Any],
            ):
                if lookup_result.cost >= self.__min_costs[lookup_result.translation]: return

                result = LookupResultWithAssociations(lookup_result, tuple(sophs_and_chords_used))

                if not api.validate_lookup_result.emit_and_validate_with_states(
                    states,
                    result=result,
                    trie=trie,
                    outline=outline,
                    original_outline=original_outline,
                ):
                    return

                self.__min_costs[lookup_result.translation] = lookup_result.cost
                self.__min_cost_results[lookup_result.translation] = result


            def __get_sorted_min_translations(self):
                return sorted(self.__min_cost_results.values(), key=lambda result: result.lookup_result.cost)


            @staticmethod
            def build(outline: tuple[Stroke, ...], original_outline: tuple[Stroke, ...], states: dict[int, Any]):
                builder = MinTranslationBuilder()
                for lookup_result, associations in LookupRunner.get_processed_lookup_results(outline):
                    builder.__record_lookup_result_if_has_min_cost(lookup_result, associations, outline, original_outline, states)
                
                return builder.__get_sorted_min_translations()


        @base_hooks.lookup.listen(soph_trie)
        def _(stroke_stenos: tuple[str, ...], translations: list[str], **_) -> "str | None":
            original_outline = tuple(Stroke.from_steno(steno) for steno in stroke_stenos)


            states = api.begin_lookup.emit_and_store_outputs(outline=original_outline)


            if len(original_outline[0]) == 0: return None # TODO


            outline = original_outline
            for state, handler in api.process_outline.states_handlers(states):
                outline = handler(state=state, outline=outline)
                if outline is None:
                    return None
            
            
            translation_choices = MinTranslationBuilder().build(outline, original_outline, states)

            # if debug:
            #     return _join_all_translations(trie, translation_choices, translations)
            
            if len(translation_choices) == 0: return None


            for state, handler in api.select_translation.states_handlers(states):
                translation = handler(state=state, trie=trie, choices=translation_choices, translations=translations, outline=outline, original_outline=original_outline)
                if translation is None:
                    continue

                return translation


            return None


        ### Reverse lookup ##############################################################


        # reverse_lookups: dict[int, Callable[[EntryIndex], Iterable[LookupResult[EntryIndex]]]] = {}


        # @base_hooks.reverse_lookup.listen(soph_trie)
        # def _(translation: str, reverse_translations: dict[str, list[EntryIndex]]):
        #     if id(trie) in reverse_lookups:
        #         reverse_lookup = reverse_lookups[id(trie)]
        #     else:
        #         reverse_lookup = trie.build_reverse_lookup()
        #         reverse_lookups[id(trie)] = reverse_lookup

            
        #     for entry_id in reverse_translations[translation]:
        #         for lookup_result in reverse_lookup(entry_id):
        #             outline: list[Stroke] = []
        #             latest_stroke: Stroke = Stroke.from_integer(0)
        #             invalid = False
        #             for transition in lookup_result.transitions:
        #                 if transition.key_id is None: continue
        #                 key = trie.get_key(transition.key_id)

        #                 if key == TRIE_STROKE_BOUNDARY_KEY:
        #                     outline.append(latest_stroke)
        #                     latest_stroke = Stroke.from_integer(0)
        #                     continue

        #                 # if key == TRIE_LINKER_KEY:
        #                 #     key_stroke = amphitheory.spec.LINKER_CHORD
        #                 # else: 
        #                 key_stroke = Stroke.from_steno(key)

        #                 if banks_info.can_add_stroke_on(latest_stroke, key_stroke):
        #                     latest_stroke += key_stroke
        #                 else:
        #                     invalid = True
        #                     break

        #             if invalid:
        #                 continue


        #             outline.append(latest_stroke)


        #             final_outline = tuple(outline)


        #             states = api.begin_lookup.emit_and_store_outputs(outline=final_outline)

        #             if not api.validate_lookup_result.emit_and_validate_with_states(
        #                 states,
        #                 result=result,
        #                 trie=trie,
        #                 outline=final_outline,
        #                 original_outline=final_outline,
        #             ):
        #                 return

        #             yield tuple(stroke.rtfcre for stroke in outline)
        

        return api

    return plugin