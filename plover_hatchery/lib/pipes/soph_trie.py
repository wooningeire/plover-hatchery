from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, NamedTuple, Protocol, final

from plover.steno import Stroke
from plover_hatchery_lib_rs import DefView, DefViewCursor, DefViewItem, Keysymbol, Sopheme, SophemeSeq

from plover_hatchery.lib.pipes.Hook import Hook
from plover_hatchery.lib.pipes.Plugin import GetPluginApi, Plugin, define_plugin
from plover_hatchery.lib.pipes.floating_keys import floating_keys
from plover_hatchery.lib.pipes.plugin_utils import iife, join_sophs_to_chords_dicts
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie, NodeSrc, Trie, TriePath, JoinedTriePaths, TransitionCostKey, TransitionKey
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.types import Soph



class SophChordAssociation(NamedTuple):
    sophs: tuple[Soph, ...]
    chord: Stroke
    chord_starts_new_stroke: bool
    phonemes: tuple[DefViewCursor, ...]
    transitions: tuple[TransitionKey, ...]

class LookupResultWithAssociations(NamedTuple):
    lookup_result: LookupResult
    sophs_and_chords_used: tuple[SophChordAssociation, ...]


class SophChordAssociationWithUnresolvedPhonemes(NamedTuple):
    sophs: tuple[Soph, ...]
    chord: Stroke
    chord_starts_new_stroke: bool
    transitions: tuple[TransitionKey, ...]


@dataclass(frozen=True)
class SophsToTranslationSearchPath:
    trie_path: TriePath = field(default_factory=TriePath)
    sophs_and_chords_used: tuple[SophChordAssociationWithUnresolvedPhonemes, ...] = ()


@dataclass(frozen=True)
class ChordToSophSearchResult:
    sophs: tuple[Soph, ...]
    chord: Stroke


class ChordToSophSearchResultWithSrcIndex(NamedTuple):
    soph_result: ChordToSophSearchResult
    chord_start_key_index: int


@final
@dataclass
class SophTrieApi:
    class BeginAddEntry(Protocol):
        def __call__(self, *, trie: NondeterministicTrie[Soph], entry_id: int) -> Any: ...
    class AddSophTransition(Protocol):
        def __call__(
            self,
            *,
            state: Any,
            cursor: DefViewCursor,
            sophs: set[Soph],
            paths: JoinedTriePaths,
            node_srcs: tuple[NodeSrc, ...],
            new_node_srcs: list[NodeSrc],
            trie: NondeterministicTrie[Soph],
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
            results: tuple[ChordToSophSearchResultWithSrcIndex, ...],
        ) -> Iterable[ChordToSophSearchResultWithSrcIndex]: ...
    class ValidateLookupResult(Protocol):
        def __call__(
            self,
            *,
            state: Any,
            result: LookupResultWithAssociations,
            trie: NondeterministicTrie[Soph],
            original_outline: tuple[Stroke, ...],
            outline: tuple[Stroke, ...],
        ) -> bool: ...
    class SelectTranslation(Protocol):
        def __call__(
            self,
            *,
            state: Any,
            trie: NondeterministicTrie[Soph],
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

    
            

    trie: NondeterministicTrie[Soph]
    transition_data: dict[TransitionCostKey, DefViewCursor]

    def register_transition(self, transition: TransitionKey, entry_id: int, phoneme: DefViewCursor):
        cost_key = TransitionCostKey(transition, entry_id)
        self.transition_data[cost_key] = phoneme


    begin_add_entry = Hook(BeginAddEntry)
    add_soph_transition = Hook(AddSophTransition)
    begin_lookup = Hook(BeginLookup)
    process_outline = Hook(ProcessOutline)
    consume_key = Hook(ConsumeKey)
    validate_lookup_result = Hook(ValidateLookupResult)
    select_translation = Hook(SelectTranslation)
    modify_translation = Hook(ModifyTranslation)


def soph_trie(
    *,
    map_to_sophs: Callable[[DefViewCursor], Iterable[str]],
    sophs_to_chords_dicts: Iterable[dict[str, str]],
) -> Plugin[SophTrieApi]:
    sophs_to_chords = join_sophs_to_chords_dicts(sophs_to_chords_dicts)


    @define_plugin(soph_trie)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_):
        from plover_hatchery.Store import store

        floating_keys_api = get_plugin_api(floating_keys)


        trie = NondeterministicTrie[Soph]()
        transition_phonemes: dict[TransitionCostKey, DefViewCursor] = {}

        store.trie = trie

        api = SophTrieApi(trie, transition_phonemes)



        ### Lookup building #############################################################
        # We construct a nondeterministic trie whose transitions are sophs, gathered from an entry's phonemes.
        # The translations are the translations of each sopheme sequence.

        @base_hooks.add_entry.listen(soph_trie)
        def _(view: DefView, entry_id: int, **_):
            states = api.begin_add_entry.emit_and_store_outputs(trie=trie, entry_id=entry_id)


            src_nodes: list[NodeSrc] = [NodeSrc(0)]
            positions_and_src_nodes_stack: list[tuple[DefViewCursor, list[NodeSrc]]] = []


            def step_in(cursor: DefViewCursor):
                while cursor.stack_len > len(positions_and_src_nodes_stack):
                    positions_and_src_nodes_stack.append((cursor, list(src_nodes)))

            def step_out(n_steps: int):
                nonlocal src_nodes


                has_keysymbols = False
                new_src_nodes: list[NodeSrc] = []


                dst_node_id = None
                for _ in range(n_steps):
                    old_cursor, old_src_nodes = positions_and_src_nodes_stack.pop()

                    match old_cursor.tip():
                        case DefViewItem.Keysymbol(keysymbol):
                            has_keysymbols = True

                            if keysymbol.optional:
                                new_src_nodes.extend(NodeSrc.increment_costs(old_src_nodes, 5))

                        case _:
                            if not has_keysymbols:
                                new_src_nodes.extend(old_src_nodes)

    

                    sophs = set(Soph(value) for value in map_to_sophs(old_cursor))
                    paths = trie.link_join(old_src_nodes, dst_node_id, sophs, entry_id)
                    if dst_node_id is None and paths.dst_node_id is not None:
                        dst_node_id = paths.dst_node_id

                    for seq in paths.transition_seqs:
                        api.register_transition(seq.transitions[0], entry_id, old_cursor)

                    api.add_soph_transition.emit_with_states(
                        states,
                        cursor=old_cursor,
                        sophs=sophs,
                        paths=paths,
                        node_srcs=tuple(old_src_nodes),
                        new_node_srcs=src_nodes,
                        trie=trie,
                        entry_id=entry_id,
                    )


                if dst_node_id is not None:
                    new_src_nodes.append(NodeSrc(dst_node_id))


                src_nodes = new_src_nodes


            @view.foreach
            def _(cursor: DefViewCursor):
                nonlocal src_nodes

                if cursor.stack_len <= len(positions_and_src_nodes_stack):


                    dst_node_id = step_out(len(positions_and_src_nodes_stack) - cursor.stack_len + 1)
                    if dst_node_id is not None:
                        src_nodes.append(NodeSrc(dst_node_id))


                step_in(cursor)



            step_out(len(positions_and_src_nodes_stack))

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
                self.__chords_to_sophs: Trie[str, list[ChordToSophSearchResult]] = Trie()

                for sophs, chords in sophs_to_chords.items():
                    for chord in chords:
                        chord_rest, chord_floaters = floating_keys_api.split(chord)
                        result = ChordToSophSearchResult(sophs, chord)


                        dst_node = self.__chords_to_sophs.follow_chain(self.__chords_to_sophs.ROOT, chord_rest.keys())
                        existing_soph_seqs = self.__chords_to_sophs.get_translation(dst_node)
                        if existing_soph_seqs is None:
                            self.__chords_to_sophs.set_translation(dst_node, [result])
                        else:
                            existing_soph_seqs.append(result)


            def begin_search(self):
                return ChordToSophSearcher.Session(self)


            @property
            def chords_to_sophs(self):
                return self.__chords_to_sophs


            class Session:
                def __init__(self, chord_finder: "ChordToSophSearcher"):
                    self.__chord_finder = chord_finder
                    self.__node_data_for_chords_to_sophs_lookup: list[ChordToSophSearchNode] = []
                    self.__current_key_index = 0
                    self.__key_starts_new_stroke = True


                def possible_sophs_after_consuming(self, key: str):
                    # Add a root node to trigger a new traversal starting from the root
                    self.__node_data_for_chords_to_sophs_lookup.append(ChordToSophSearchNode(chord_finder.chords_to_sophs.ROOT, self.__current_key_index ))


                    # Continue the ongoing trie traversals
                    new_node_indices: list[ChordToSophSearchNode] = []

                    for trie_node in self.__node_data_for_chords_to_sophs_lookup:
                        dst_node = self.__chord_finder.chords_to_sophs.traverse(trie_node.trie_node, key)
                        if dst_node is None: continue

                        new_node_indices.append(ChordToSophSearchNode(dst_node, trie_node.chord_starting_key_index))

                        soph_results = self.__chord_finder.chords_to_sophs.get_translation(dst_node)

                        if soph_results is None: continue


                        for soph_result in soph_results:
                            yield ChordToSophSearchResultWithSrcIndex(soph_result, trie_node.chord_starting_key_index)


                    self.__node_data_for_chords_to_sophs_lookup = new_node_indices
                    self.__current_key_index += 1
                    self.__key_starts_new_stroke = False

                
                def finish_stroke(self):
                    # We don't want chords to bleed across strokes, so reset them
                    self.__node_data_for_chords_to_sophs_lookup = []
                    self.__key_starts_new_stroke = True


        chord_finder = ChordToSophSearcher(sophs_to_chords_dicts)


        ### Lookup ######################################################################
        # We go key by key in the user's outline. For each key, check all possible configurations of sophs that the
        # outline could represent, traversing the nondeterministic soph trie as soon as sophs are found.
        # After consuming all the keys, find the translation with the lowest cost.

        @dataclass(frozen=True)
        class ChordToSophSearchNode:
            trie_node: int
            chord_starting_key_index: int


        class SophsToTranslationPathFinder:
            """Manages the key-by-key iteration phase of lookup."""


            def __init__(self):
                self.__possible_soph_paths: list[list[SophsToTranslationSearchPath]] = [[SophsToTranslationSearchPath()]]
                self.__chord_search = chord_finder.begin_search()
                self.__consumed_keys: list[str] = []
                self.__is_new_stroke = True


            def __stroke_has_required_floaters(self, result: ChordToSophSearchResultWithSrcIndex, stroke: Stroke):
                return floating_keys_api.only_floaters(result.soph_result.chord) in stroke
            


            def __new_paths_ending_with_soph(self, result: ChordToSophSearchResultWithSrcIndex):
                for path in self.__possible_soph_paths[result.chord_start_key_index]:
                    for new_trie_path in trie.traverse_chain((path.trie_path,), result.soph_result.sophs):
                        yield SophsToTranslationSearchPath(
                            new_trie_path,
                            path.sophs_and_chords_used + (
                                SophChordAssociationWithUnresolvedPhonemes(
                                    result.soph_result.sophs,
                                    result.soph_result.chord,
                                    self.__is_new_stroke,
                                    new_trie_path.transitions[len(path.trie_path.transitions):]
                                ),
                            )
                        )

            
            def __all_sophs_after_consuming(self, key: str, states: dict[int, Any]):
                results = list(self.__chord_search.possible_sophs_after_consuming(key))

                for state, handler in api.consume_key.states_handlers(states):
                    results.extend(handler(state=state, key=key, key_index=len(self.__consumed_keys), is_new_stroke=self.__is_new_stroke, results=tuple(results)))

                yield from results


            def __consume_key(self, key: str, stroke: Stroke, states: dict[int, Any]):
                new_possible_sophs: list[SophsToTranslationSearchPath] = []


                for result in self.__all_sophs_after_consuming(key, states):
                    if not self.__stroke_has_required_floaters(result, stroke): continue

                    new_possible_sophs.extend(self.__new_paths_ending_with_soph(result))


                self.__possible_soph_paths.append(new_possible_sophs)
                self.__consumed_keys.append(key)
                self.__is_new_stroke = False
            

            def __finish_stroke(self):
                self.__chord_search.finish_stroke()
                self.__is_new_stroke = True


            def __get_final_paths(self):
                return self.__possible_soph_paths[-1]


            @staticmethod
            def get_paths_from_outline(outline: tuple[Stroke, ...], states: dict[int, Any]):
                soph_path_finder = SophsToTranslationPathFinder()

                for stroke_index, stroke in enumerate(outline):
                    if stroke_index > 0:
                        soph_path_finder.__finish_stroke()

                    for key in stroke - floating_keys_api.floaters:
                        soph_path_finder.__consume_key(key, stroke, states)

                return soph_path_finder.__get_final_paths()


        @iife
        def get_processed_lookup_results():
            """Manages lookup results after they have been found by a lookup session."""


            def resolve_phonemes(lookup_result: LookupResult, association: SophChordAssociationWithUnresolvedPhonemes):
                phonemes: list[DefViewCursor] = []
                for transition in association.transitions:
                    cost_key = TransitionCostKey(transition, lookup_result.translation_id)
                    if cost_key not in transition_phonemes: continue

                    phonemes.append(transition_phonemes[cost_key])
                
                return tuple(phonemes)


            def get_processed_lookup_results(outline: tuple[Stroke, ...], states: dict[int, Any]):
                for final_path in SophsToTranslationPathFinder.get_paths_from_outline(outline, states):
                    for lookup_result in trie.get_translations_and_costs((final_path.trie_path,)):
                        new_associations = tuple(
                            SophChordAssociation(
                                association.sophs,
                                association.chord,
                                association.chord_starts_new_stroke,
                                resolve_phonemes(lookup_result, association),
                                association.transitions,
                            )
                            for association in final_path.sophs_and_chords_used
                        )

                        yield lookup_result, new_associations


            return get_processed_lookup_results




        class MinTranslationBuilder:
            def __init__(self):
                self.__min_costs_by_translation_id: dict[int, float] = defaultdict(lambda: float("inf"))
                self.__min_cost_results_by_translation_id: dict[int, LookupResultWithAssociations] = {}


            def __record_lookup_result_if_has_min_cost(
                self,
                lookup_result: LookupResult,
                sophs_and_chords_used: Iterable[SophChordAssociation],
                outline: tuple[Stroke, ...],
                original_outline: tuple[Stroke, ...],
                states: dict[int, Any],
            ):
                if lookup_result.cost >= self.__min_costs_by_translation_id[lookup_result.translation_id]: return

                result = LookupResultWithAssociations(lookup_result, tuple(sophs_and_chords_used))

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


        @base_hooks.lookup.listen(soph_trie)
        def _(stroke_stenos: tuple[str, ...], translations: list[str], **_) -> str | None:
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