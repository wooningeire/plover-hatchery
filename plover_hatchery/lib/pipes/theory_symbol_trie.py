from collections import defaultdict
from dataclasses import dataclass
import json
from typing import Any, Callable, Iterable, NamedTuple, Protocol, Sequence, final

from plover.steno import Stroke

from plover_hatchery_lib_rs import DefView, DefViewCursor, add_theory_symbol_trie_entry, ChordToTheorySymbolSearchNode as RsChordToTheorySymbolSearchNode, ChordToTheorySymbolSearchResult, ChordToTheorySymbolSearcher as RsChordToTheorySymbolSearcher, TheorySymbolsToTranslationSearchPath, TriePath, TransitionCostKey, TransitionKey, TheorySymbol, TransitionFlagManager
from plover_hatchery.lib.pipes.Hook import Hook
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.floating_keys import floating_keys
from plover_hatchery.lib.pipes.plugin_utils import iife, join_theory_symbols_to_chords_dicts
from plover_hatchery.lib.trie import KeyIdManager, LookupResult, NondeterministicTrie, TransitionSourceNode, JoinedTriePaths
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks



class TheorySymbolChordAssociation(NamedTuple):
    theory_symbols: tuple[TheorySymbol, ...]
    chord: Stroke
    chord_starts_new_stroke: bool
    phonemes: tuple[DefViewCursor, ...]
    transitions: Sequence[TransitionKey]

class LookupResultWithAssociations(NamedTuple):
    lookup_result: LookupResult
    theory_symbols_and_chords_used: tuple[TheorySymbolChordAssociation, ...]


class TheorySymbolChordAssociationWithUnresolvedPhonemes(NamedTuple):
    theory_symbols: tuple[TheorySymbol, ...]
    chord: Stroke
    chord_starts_new_stroke: bool
    transitions: Sequence[TransitionKey]


class ChordToTheorySymbolSearchResultWithSrcIndex(NamedTuple):
    theory_symbol_result: ChordToTheorySymbolSearchResult
    chord_start_key_index: int


@final
@dataclass
class TheorySymbolTrieApi:
    class BeginAddEntry(Protocol):
        def __call__(self, *, trie: NondeterministicTrie, entry_id: int) -> Any: ...
    class AddTheorySymbolTransition(Protocol):
        def __call__(
            self,
            *,
            state: Any,
            cursor: DefViewCursor,
            theory_symbols: set[TheorySymbol],
            paths: JoinedTriePaths,
            node_srcs: tuple[TransitionSourceNode, ...],
            new_node_srcs: list[TransitionSourceNode],
            trie: NondeterministicTrie,
            entry_id: int,
        ): ...
    class BeginLookup(Protocol):
        def __call__(self, *, outline: tuple[Stroke, ...]) -> Any: ...
    class ProcessOutline(Protocol):
        def __call__(self, *, state: Any, outline: tuple[Stroke, ...]) -> tuple[Stroke, ...] | None: ...
    class ConsumeKey(Protocol):
        def __call__(
            self,
            *,
            state: Any,
            key: str,
            key_index: int,
            is_new_stroke: bool,
            results: tuple[ChordToTheorySymbolSearchResultWithSrcIndex, ...],
        ) -> Iterable[ChordToTheorySymbolSearchResultWithSrcIndex]: ...
    class ValidateLookupResult(Protocol):
        def __call__(
            self,
            *,
            state: Any,
            result: LookupResultWithAssociations,
            trie: NondeterministicTrie,
            original_outline: tuple[Stroke, ...],
            outline: tuple[Stroke, ...],
        ) -> bool: ...
    class SelectTranslation(Protocol):
        def __call__(
            self,
            *,
            state: Any,
            trie: NondeterministicTrie,
            choices: list[LookupResultWithAssociations],
            translations: list[str],
            original_outline: tuple[Stroke, ...],
            outline: tuple[Stroke, ...],
        ) -> str | None: ...
    class ModifyTranslation(Protocol):
        def __call__(
            self,
            *,
            state: Any,
            translation: str,
            original_outline: tuple[Stroke, ...],
            outline: tuple[Stroke, ...],
        ) -> str: ...

    
            

    trie: NondeterministicTrie
    transition_data: dict[TransitionCostKey, DefViewCursor]
    transition_flags: TransitionFlagManager
    key_id_manager: KeyIdManager[TheorySymbol]

    def register_transition(self, transition: TransitionKey, entry_id: int, phoneme: DefViewCursor):
        cost_key = TransitionCostKey(transition, entry_id)
        self.transition_data[cost_key] = phoneme


    begin_add_entry = Hook(BeginAddEntry)
    add_theory_symbol_transition = Hook(AddTheorySymbolTransition)
    begin_lookup = Hook(BeginLookup)
    process_outline = Hook(ProcessOutline)
    consume_key = Hook(ConsumeKey)
    validate_lookup_result = Hook(ValidateLookupResult)
    select_translation = Hook(SelectTranslation)
    modify_translation = Hook(ModifyTranslation)


def theory_symbol_trie(
    *,
    map_to_theory_symbols: Callable[[DefViewCursor], set[str]],
    theory_symbols_to_chords_dicts: Iterable[dict[str, str]],
) -> Plugin[TheorySymbolTrieApi]:
    cache_key = "theory_symbol_trie"
    legacy_cache_key = "soph_trie"
    theory_symbols_to_chords = join_theory_symbols_to_chords_dicts(theory_symbols_to_chords_dicts)


    @define_plugin(theory_symbol_trie)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_):
        from plover_hatchery.Store import store

        floating_keys_api = get_plugin_api(floating_keys)


        trie = NondeterministicTrie()
        transition_phonemes: dict[TransitionCostKey, DefViewCursor] = {}
        transition_flags = TransitionFlagManager()
        key_id_manager = KeyIdManager[TheorySymbol]()

        
        skip_transition_flag = transition_flags.new_flag("skip")

        store.trie = trie

        api = TheorySymbolTrieApi(trie, transition_phonemes, transition_flags, key_id_manager)
        deferred_transition_flags_cache: tuple[str, Any] | None = None
        transition_flags_loaded = True
        subtrie_builders: dict[int, Callable[[int], dict[str, Any] | None]] = {}

        def export_transition_flags_cache():
            if not transition_flags_loaded and deferred_transition_flags_cache is not None:
                cache_kind, cache_value = deferred_transition_flags_cache
                if cache_kind == "bytes":
                    return {"transition_flags_bytes": cache_value}

                try:
                    return {
                        "transition_flags_bytes": TransitionFlagManager.from_state(
                            *cache_value
                        ).export_state_bytes()
                    }
                except AttributeError:
                    return {"transition_flags": cache_value}

            try:
                return {"transition_flags_bytes": api.transition_flags.export_state_bytes()}
            except AttributeError:
                return {"transition_flags": api.transition_flags.export_state()}

        def ensure_transition_flags_loaded():
            nonlocal deferred_transition_flags_cache, transition_flags_loaded

            if transition_flags_loaded or deferred_transition_flags_cache is None:
                return

            cache_kind, cache_value = deferred_transition_flags_cache
            if cache_kind == "bytes":
                api.transition_flags.load_state_bytes(cache_value)
            else:
                api.transition_flags.load_state(*cache_value)

            deferred_transition_flags_cache = None
            transition_flags_loaded = True

        @base_hooks.begin_build_lookup.listen(theory_symbol_trie)
        def _():
            nonlocal deferred_transition_flags_cache, transition_flags_loaded

            api.trie.load_state(NondeterministicTrie().export_state())
            api.key_id_manager.load_keys([])
            api.transition_data.clear()

            labels, _ = api.transition_flags.export_state()
            api.transition_flags.load_state(labels, [])
            deferred_transition_flags_cache = None
            transition_flags_loaded = True
            subtrie_builders.clear()

        @base_hooks.export_build_cache.listen(theory_symbol_trie)
        def _(**_):
            try:
                trie_cache = {"trie_bytes": api.trie.export_state_bytes()}
            except AttributeError:
                trie_cache = {"trie": api.trie.export_state()}

            return cache_key, {
                **trie_cache,
                "key_ids": [
                    theory_symbol.value
                    for theory_symbol in api.key_id_manager.export_keys()
                ],
                **export_transition_flags_cache(),
            }

        @base_hooks.import_build_cache.listen(theory_symbol_trie)
        def _(cache: dict[str, Any], **_):
            nonlocal deferred_transition_flags_cache, transition_flags_loaded

            data = cache.get(cache_key)
            if data is None:
                data = cache[legacy_cache_key]

            if "trie_bytes" in data:
                api.trie.load_state_bytes(data["trie_bytes"])
            else:
                api.trie.load_state(data["trie"])

            api.key_id_manager.load_keys(
                TheorySymbol(theory_symbol_value)
                for theory_symbol_value in data["key_ids"]
            )
            if "transition_flags_bytes" in data:
                deferred_transition_flags_cache = ("bytes", data["transition_flags_bytes"])
            else:
                deferred_transition_flags_cache = ("state", data["transition_flags"])
            transition_flags_loaded = False
            api.transition_data.clear()
            subtrie_builders.clear()



        ### Lookup building #############################################################
        # We construct a nondeterministic trie whose transitions are theory_symbols, gathered from an entry's phonemes.
        # The translations are the translations of each sopheme sequence.

        @base_hooks.add_entry.listen(theory_symbol_trie)
        def _(view: DefView, entry_id: int, **_):

            def map_to_theory_symbols_wrapper(cursor: DefViewCursor):
                return set(TheorySymbol(theory_symbol_label) for theory_symbol_label in map_to_theory_symbols(cursor))
                
            def get_key_ids_wrapper(theory_symbols: set[TheorySymbol]):
                return key_id_manager.get_key_ids_else_create(theory_symbols)
            
            def register_transition_wrapper(transition: TransitionKey, entry_id: int, cursor: DefViewCursor):
                api.register_transition(transition, entry_id, cursor)
                

            add_theory_symbol_trie_entry(
                trie.rs,
                entry_id,
                view,
                map_to_theory_symbols_wrapper,
                get_key_ids_wrapper,
                register_transition_wrapper,
                transition_flags,
                skip_transition_flag,
                api.begin_add_entry.emit_and_store_outputs,
                api.add_theory_symbol_transition.emit_with_states
            )
            subtrie_builders.clear()





        # @base_hooks.complete_build_lookup.listen(theory_symbol_trie)
        # def _(**_):
        #     print(trie)



        ### Chord -> theory_symbol mapping ######################################################
        # We build a trie whose transitions are keys in strokes, so we can look up the possible theory symbols
        # for each chord. We also track required chord floaters so a symbol with a floater chord, such as *T for th,
        # is only used when the user's stroke contains that floater.


        class ChordToTheorySymbolSearcher:
            """Builds the chord-key trie used to find possible theory_symbols during lookup."""

            def __init__(self, theory_symbols_to_chords_dicts: Iterable[dict[str, str]]):
                entries: list[tuple[tuple[str, ...], ChordToTheorySymbolSearchResult]] = []

                for theory_symbols, chords in theory_symbols_to_chords.items():
                    for chord in chords:
                        chord_rest, _ = floating_keys_api.split(chord)
                        entries.append((chord_rest.keys(), ChordToTheorySymbolSearchResult(theory_symbols, chord)))

                # Rust owns the trie traversal; Python keeps the hook-facing result objects.
                self.__chords_to_theory_symbols = RsChordToTheorySymbolSearcher(entries)


            def begin_search(self):
                return ChordToTheorySymbolSearcher.Session(self)


            @property
            def chords_to_theory_symbols(self):
                return self.__chords_to_theory_symbols


            class Session:
                def __init__(self, chord_finder: "ChordToTheorySymbolSearcher"):
                    self.__chord_finder = chord_finder
                    self.__node_data_for_chords_to_theory_symbols_lookup: list[RsChordToTheorySymbolSearchNode] = []
                    self.__current_key_index = 0
                    self.__key_starts_new_stroke = True


                def possible_theory_symbols_after_consuming(self, key: str):
                    # The Rust searcher handles starting a fresh root traversal and
                    # continuing active traversals for this key.
                    self.__node_data_for_chords_to_theory_symbols_lookup, theory_symbol_results = self.__chord_finder.chords_to_theory_symbols.possible_theory_symbols_after_consuming(
                        self.__node_data_for_chords_to_theory_symbols_lookup,
                        self.__current_key_index,
                        key,
                    )
                    self.__current_key_index += 1
                    self.__key_starts_new_stroke = False

                    for theory_symbol_match in theory_symbol_results:
                        yield ChordToTheorySymbolSearchResultWithSrcIndex(
                            theory_symbol_match.theory_symbol_result,
                            theory_symbol_match.chord_starting_key_index,
                        )

                
                def finish_stroke(self):
                    # We don't want chords to bleed across strokes, so reset them
                    self.__node_data_for_chords_to_theory_symbols_lookup = []
                    self.__key_starts_new_stroke = True


        chord_finder = ChordToTheorySymbolSearcher(theory_symbols_to_chords_dicts)


        ### Lookup ######################################################################
        # We go key by key in the user's outline. For each key, check all possible configurations of theory_symbols that the
        # outline could represent, traversing the nondeterministic theory_symbol trie as soon as theory_symbols are found.
        # After consuming all the keys, find the translation with the lowest cost.

        class TheorySymbolsToTranslationPathFinder:
            """Manages the key-by-key iteration phase of lookup."""


            def __init__(self):
                self.__possible_theory_symbol_paths: list[list[TheorySymbolsToTranslationSearchPath]] = [[TheorySymbolsToTranslationSearchPath()]]
                self.__chord_search = chord_finder.begin_search()
                self.__consumed_keys: list[str] = []
                self.__is_new_stroke = True


            def __stroke_has_required_floaters(self, result: ChordToTheorySymbolSearchResultWithSrcIndex, stroke: Stroke):
                return floating_keys_api.only_floaters(result.theory_symbol_result.chord) in stroke
            


            def __new_paths_ending_with_theory_symbol(self, result: ChordToTheorySymbolSearchResultWithSrcIndex):
                for path in self.__possible_theory_symbol_paths[result.chord_start_key_index]:
                    for new_trie_path in trie.traverse_chain((path.trie_path,), key_id_manager.get_key_ids_else_create(result.theory_symbol_result.theory_symbols)):
                        yield TheorySymbolsToTranslationSearchPath(
                            new_trie_path,
                            path.theory_symbols_and_chords_used + (
                                TheorySymbolChordAssociationWithUnresolvedPhonemes(
                                    result.theory_symbol_result.theory_symbols,
                                    result.theory_symbol_result.chord,
                                    self.__is_new_stroke,
                                    new_trie_path.transitions[len(path.trie_path.transitions):]
                                ),
                            )
                        )

            
            def __all_theory_symbols_after_consuming(self, key: str, states: dict[int, Any]):
                results = list(self.__chord_search.possible_theory_symbols_after_consuming(key))

                for state, handler in api.consume_key.states_handlers(states):
                    results.extend(handler(state=state, key=key, key_index=len(self.__consumed_keys), is_new_stroke=self.__is_new_stroke, results=tuple(results)))

                yield from results


            def __consume_key(self, key: str, stroke: Stroke, states: dict[int, Any]):
                new_possible_theory_symbols: list[TheorySymbolsToTranslationSearchPath] = []


                for result in self.__all_theory_symbols_after_consuming(key, states):
                    if not self.__stroke_has_required_floaters(result, stroke): continue

                    new_possible_theory_symbols.extend(self.__new_paths_ending_with_theory_symbol(result))


                self.__possible_theory_symbol_paths.append(new_possible_theory_symbols)
                self.__consumed_keys.append(key)
                self.__is_new_stroke = False
            

            def __finish_stroke(self):
                self.__chord_search.finish_stroke()
                self.__is_new_stroke = True


            def __get_final_paths(self):
                return self.__possible_theory_symbol_paths[-1]


            @staticmethod
            def get_paths_from_outline(outline: tuple[Stroke, ...], states: dict[int, Any]):
                theory_symbol_path_finder = TheorySymbolsToTranslationPathFinder()

                for stroke_index, stroke in enumerate(outline):
                    if stroke_index > 0:
                        theory_symbol_path_finder.__finish_stroke()

                    for key in stroke - floating_keys_api.floaters:
                        theory_symbol_path_finder.__consume_key(key, stroke, states)

                return theory_symbol_path_finder.__get_final_paths()


        @iife
        def get_processed_lookup_results_with_paths():
            """Manages lookup results after they have been found by a lookup session."""


            def resolve_phonemes(lookup_result: LookupResult, association: TheorySymbolChordAssociationWithUnresolvedPhonemes):
                phonemes: list[DefViewCursor] = []
                for transition in association.transitions:
                    cost_key = TransitionCostKey(transition, lookup_result.translation_id)
                    if cost_key not in transition_phonemes: continue

                    phonemes.append(transition_phonemes[cost_key])
                
                return tuple(phonemes)


            def get_processed_lookup_results_with_paths(outline: tuple[Stroke, ...], states: dict[int, Any]):
                for final_path in TheorySymbolsToTranslationPathFinder.get_paths_from_outline(outline, states):
                    for lookup_result in trie.get_translations_and_costs((final_path.trie_path,)):
                        new_associations = tuple(
                            TheorySymbolChordAssociation(
                                association.theory_symbols,
                                association.chord,
                                association.chord_starts_new_stroke,
                                resolve_phonemes(lookup_result, association),
                                association.transitions,
                            )
                            for association in final_path.theory_symbols_and_chords_used
                        )

                        yield final_path, lookup_result, new_associations


            return get_processed_lookup_results_with_paths


        def get_processed_lookup_results(outline: tuple[Stroke, ...], states: dict[int, Any]):
            for _final_path, lookup_result, associations in get_processed_lookup_results_with_paths(outline, states):
                yield lookup_result, associations




        class MinTranslationBuilder:
            def __init__(self):
                self.__min_costs_by_translation_id: dict[int, float] = defaultdict(lambda: float("inf"))
                self.__min_cost_results_by_translation_id: dict[int, LookupResultWithAssociations] = {}


            def __record_lookup_result_if_has_min_cost(
                self,
                lookup_result: LookupResult,
                theory_symbols_and_chords_used: Iterable[TheorySymbolChordAssociation],
                outline: tuple[Stroke, ...],
                original_outline: tuple[Stroke, ...],
                states: dict[int, Any],
            ):
                if lookup_result.cost >= self.__min_costs_by_translation_id[lookup_result.translation_id]: return

                result = LookupResultWithAssociations(lookup_result, tuple(theory_symbols_and_chords_used))

                if not api.validate_lookup_result.emit_and_validate_with_states(
                    states,
                    result=result,
                    trie=trie,
                    outline=outline,
                    original_outline=original_outline,
                ):
                    return

                self.__min_costs_by_translation_id[lookup_result.translation_id] = lookup_result.cost
                self.__min_cost_results_by_translation_id[lookup_result.translation_id] = result


            def __get_sorted_min_translations(self):
                return sorted(self.__min_cost_results_by_translation_id.values(), key=lambda result: result.lookup_result.cost)


            @staticmethod
            def build(outline: tuple[Stroke, ...], original_outline: tuple[Stroke, ...], states: dict[int, Any]):
                builder = MinTranslationBuilder()
                for lookup_result, associations in get_processed_lookup_results(outline, states):
                    builder.__record_lookup_result_if_has_min_cost(lookup_result, associations, outline, original_outline, states)
                
                return builder.__get_sorted_min_translations()


        @base_hooks.lookup.listen(theory_symbol_trie)
        def _(stroke_stenos: tuple[str, ...], translations: list[str], **_) -> str | None:
            original_outline = tuple(Stroke.from_steno(steno) for steno in stroke_stenos)


            states = api.begin_lookup.emit_and_store_outputs(outline=original_outline)


            if len(original_outline[0]) == 0: return None # TODO


            outline = original_outline
            for state, handler in api.process_outline.states_handlers(states):
                outline = handler(state=state, outline=outline)
                if outline is None:
                    return None
            
            
            translation_choices = MinTranslationBuilder.build(outline, original_outline, states)
            
            if len(translation_choices) == 0: return None


            translation = None


            for state, handler in api.select_translation.states_handlers(states):
                translation = handler(state=state, trie=trie, choices=translation_choices, translations=translations, outline=outline, original_outline=original_outline)
                if translation is not None:
                    break


            if translation is None:
                return


            for state, handler in api.modify_translation.states_handlers(states):
                translation = handler(state=state, translation=translation, outline=outline, original_outline=original_outline)


            return translation


        @base_hooks.breakdown_lookup.listen(theory_symbol_trie)
        def _(stroke_stenos: tuple[str, ...], translations: list[str], **_):
            original_outline = tuple(Stroke.from_steno(steno) for steno in stroke_stenos)


            states = api.begin_lookup.emit_and_store_outputs(outline=original_outline)


            if len(original_outline[0]) == 0: return None # TODO


            outline = original_outline
            for state, handler in api.process_outline.states_handlers(states):
                outline = handler(state=state, outline=outline)
                if outline is None:
                    return None
            
            
            def transition_cost_or_none(transition: TransitionKey, translation_id: int):
                try:
                    return trie.get_transition_cost(transition, translation_id)
                except KeyError:
                    return None

            def summarize_transition(
                transition: TransitionKey,
                *,
                translation_id: int,
                dst_node_id: int,
            ):
                return {
                    "key": api.key_id_manager.get_key_str(transition.key_id),
                    "cost": transition_cost_or_none(transition, translation_id),
                    "src_node_id": transition.src_node_index,
                    "dst_node_id": dst_node_id,
                }

            def nodes_by_association_for_final_path(final_path: TheorySymbolsToTranslationSearchPath):
                nodes_by_association: list[Sequence[int]] = []

                for i, association in enumerate(final_path.theory_symbols_and_chords_used):
                    if i == len(final_path.theory_symbols_and_chords_used) - 1:
                        next_node = final_path.trie_path.dst_node_id
                    else:
                        next_node = final_path.theory_symbols_and_chords_used[i + 1].transitions[0].src_node_index

                    nodes_by_association.append((
                        *(transition.src_node_index for transition in association.transitions),
                        next_node,
                    ))

                return nodes_by_association

            def summarize_association(
                association: TheorySymbolChordAssociation,
                *,
                nodes: Sequence[int],
                translation_id: int,
            ):
                return {
                    "theory_symbols": [
                        theory_symbol.value
                        for theory_symbol in association.theory_symbols
                    ],
                    "chord": association.chord.rtfcre,
                    "starts_new_stroke": association.chord_starts_new_stroke,
                    "nodes": nodes,
                    "transitions": [
                        summarize_transition(
                            transition,
                            translation_id=translation_id,
                            dst_node_id=nodes[i + 1],
                        )
                        for i, transition in enumerate(association.transitions)
                    ],
                }

            def summarize_lookup_result(
                final_path: TheorySymbolsToTranslationSearchPath,
                result: LookupResultWithAssociations,
            ):
                translation_id = result.lookup_result.translation_id
                nodes_by_association = nodes_by_association_for_final_path(final_path)

                return {
                    "translation": translations[translation_id],
                    "entry_id": translation_id,
                    "translation_id": translation_id,
                    "cost": result.lookup_result.cost,
                    "path": [
                        summarize_association(
                            association,
                            nodes=nodes_by_association[i],
                            translation_id=translation_id,
                        )
                        for i, association in enumerate(final_path.theory_symbols_and_chords_used)
                    ],
                }

            min_costs_by_translation_id: dict[int, float] = defaultdict(lambda: float("inf"))
            summaries_by_translation_id: dict[int, dict[str, Any]] = {}

            for final_path, lookup_result, associations in get_processed_lookup_results_with_paths(outline, states):
                translation_id = lookup_result.translation_id
                if lookup_result.cost >= min_costs_by_translation_id[translation_id]:
                    continue

                result = LookupResultWithAssociations(lookup_result, tuple(associations))
                if not api.validate_lookup_result.emit_and_validate_with_states(
                    states,
                    result=result,
                    trie=trie,
                    outline=outline,
                    original_outline=original_outline,
                ):
                    continue

                min_costs_by_translation_id[translation_id] = lookup_result.cost
                summaries_by_translation_id[translation_id] = summarize_lookup_result(final_path, result)

            summaries = sorted(
                summaries_by_translation_id.values(),
                key=lambda summary: summary["cost"],
            )

            return json.dumps(summaries)


        ### Reverse lookup ##############################################################

        @base_hooks.breakdown_translation.listen(theory_symbol_trie)
        def _(translation: str, entries: list[str], reverse_translations: dict[str, list[int]], **_):
            ensure_transition_flags_loaded()

            if id(trie) in subtrie_builders:
                subtrie_builder = subtrie_builders[id(trie)]
            else:
                subtrie_builder = trie.build_subtrie_builder(transition_flags, key_id_manager.get_key_str)
                subtrie_builders[id(trie)] = subtrie_builder

            breakdowns = []
            for entry_id in reverse_translations.get(translation, []):
                if entry_id >= len(entries):
                    continue

                subtrie = subtrie_builder(entry_id)
                if subtrie is None:
                    continue

                breakdowns.append({
                    "entry": entries[entry_id],
                    "subtrie": subtrie,
                })

            return json.dumps(breakdowns)

        # reverse_lookups: dict[int, Callable[[int], Iterable[LookupResult[int]]]] = {}


        # @base_hooks.reverse_lookup.listen(theory_symbol_trie)
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
