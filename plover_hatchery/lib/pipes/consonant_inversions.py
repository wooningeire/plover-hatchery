import itertools
from typing import Any, Generator


from dataclasses import dataclass, field

from plover.steno import Stroke
from plover_hatchery_lib_rs import DefViewCursor, DefViewItem
from plover_hatchery.lib.pipes.Plugin import define_plugin, GetPluginApi
from plover_hatchery.lib.pipes.theory_symbol_trie import ChordToTheorySymbolSearchResult, ChordToTheorySymbolSearchResultWithSrcIndex, LookupResultWithAssociations, TheorySymbolChordAssociation, TheorySymbolsToTranslationSearchPath, theory_symbol_trie
from plover_hatchery_lib_rs import TheorySymbol, TransitionFlagManager
from plover_hatchery.lib.trie import NondeterministicTrie, TransitionSourceNode, JoinedTriePaths, TransitionFlag, TransitionCostKey



def consonant_inversions(*, consonant_theory_symbols_str: str, inversion_domains_steno: str):
    consonant_theory_symbols = set(TheorySymbol(value) for value in consonant_theory_symbols_str.split())
    inversion_domains: tuple[Stroke, ...] = tuple(
        sorted(
            Stroke.from_steno(domain_steno) for domain_steno in inversion_domains_steno.split()
        )
    )

    @define_plugin(consonant_inversions)
    def plugin(get_plugin_api: GetPluginApi, **_):
        theory_symbol_trie_api = get_plugin_api(theory_symbol_trie)

        inversion_flag = theory_symbol_trie_api.transition_flags.new_flag("inversion")


        @dataclass(frozen=True)
        class PastConsonant:
            node_srcs: tuple[TransitionSourceNode, ...]
            theory_symbols: tuple[TheorySymbol, ...]
            cursor: DefViewCursor


        class ConsonantInversionsAddEntryState:
            def __init__(self):
                self.past_consonants: list[PastConsonant] = []


        @theory_symbol_trie_api.begin_add_entry.listen(consonant_inversions)
        def _(**_):
            return ConsonantInversionsAddEntryState()


        def create_inversion_theory_symbol(theory_symbols: "tuple[TheorySymbol, ...]"):
            sorted_theory_symbols = sorted(theory_symbols, key=lambda theory_symbol: theory_symbol.value)
            return TheorySymbol(f"inversion:{' '.join(theory_symbol.value for theory_symbol in sorted_theory_symbols)}")

        def get_inversion_theory_symbols(past_consonants: list[PastConsonant]):
            def get_product_choices():
                for consonant in past_consonants:
                    keysymbol = consonant.cursor.tip().keysymbol()

                    if keysymbol.optional:
                        yield (*consonant.theory_symbols, None)
                    else:
                        yield consonant.theory_symbols

            for combo in itertools.product(*get_product_choices()):
                non_null_theory_symbols = tuple(
                    theory_symbol
                    for theory_symbol in combo
                    if theory_symbol is not None
                )
                if len(non_null_theory_symbols) <= 1: continue

                yield create_inversion_theory_symbol(non_null_theory_symbols)


        @theory_symbol_trie_api.add_theory_symbol_transition.listen(consonant_inversions)
        def _(
            state: ConsonantInversionsAddEntryState,
            theory_symbols: set[TheorySymbol],
            cursor: DefViewCursor,
            paths: JoinedTriePaths,
            node_srcs: tuple[TransitionSourceNode, ...],
            trie: NondeterministicTrie,
            entry_id: int,
            **_,
        ):
            match cursor.tip():
                case DefViewItem.Keysymbol(keysymbol):
                    pass

                case _:
                    return

            if any(theory_symbol not in consonant_theory_symbols for theory_symbol in theory_symbols):
                keysymbol = cursor.tip().keysymbol()

                # TODO verify this
                if not keysymbol.optional:
                    state.past_consonants = []
                    
                return

            current_consonant_theory_symbols = tuple(theory_symbols & consonant_theory_symbols)
            if len(current_consonant_theory_symbols) == 0: return

            state.past_consonants.append(PastConsonant(node_srcs, current_consonant_theory_symbols, cursor))

            if paths.dst_node_id is not None:
                for i, consonant in enumerate(state.past_consonants[:-1]):
                    inversion_theory_symbols = get_inversion_theory_symbols(state.past_consonants[i:])
                    new_paths = trie.link_join(
                        tuple(TransitionSourceNode.increment_costs(consonant.node_srcs, 50)),
                        paths.dst_node_id,
                        theory_symbol_trie_api.key_id_manager.get_key_ids_else_create(inversion_theory_symbols),
                        entry_id
                    )

                    for transition_seq in new_paths.transition_seqs:
                        for transition in transition_seq.transitions:
                            theory_symbol_trie_api.transition_flags.flag_transition(TransitionCostKey(transition, entry_id), inversion_flag)




        def get_inversion_domain_of_stroke(stroke: Stroke):
            domains = tuple(filter(lambda domain: len(domain & stroke) > 0, inversion_domains))

            if len(domains) != 1:
                return None

            return domains[0]


        @dataclass
        class ConsonantInversionsLookupState:
            current_domain: Stroke | None = None
            theory_symbols_in_current_domain: list[tuple[ChordToTheorySymbolSearchResultWithSrcIndex, ...]] = field(default_factory=list)
            first_key_index_in_current_domain: int = -1

            def paths_ending_with(self, result: ChordToTheorySymbolSearchResultWithSrcIndex, current_chain: tuple[ChordToTheorySymbolSearchResultWithSrcIndex, ...]=()) -> Generator[tuple[ChordToTheorySymbolSearchResultWithSrcIndex, ...], None, None]:
                if result.chord_start_key_index < self.first_key_index_in_current_domain:
                    return

                if result.chord_start_key_index == self.first_key_index_in_current_domain:
                    yield (result, *current_chain)

                for old_result in self.theory_symbols_in_current_domain[result.chord_start_key_index - self.first_key_index_in_current_domain]:
                    if old_result in current_chain or old_result == result: continue

                    yield from self.paths_ending_with(old_result, (result, *current_chain))


        @theory_symbol_trie_api.begin_lookup.listen(consonant_inversions)
        def _(**_):
            return ConsonantInversionsLookupState()


        @theory_symbol_trie_api.consume_key.listen(consonant_inversions)
        def _(state: ConsonantInversionsLookupState, key: str, key_index: int, is_new_stroke: bool, results: tuple[ChordToTheorySymbolSearchResultWithSrcIndex, ...], **_):
            inversion_domain = get_inversion_domain_of_stroke(Stroke.from_keys((key,)))
            if inversion_domain is None:
                # Nullify the state's inversion domain
                state.current_domain = None
                state.theory_symbols_in_current_domain = []
                state.first_key_index_in_current_domain = -1
                return

            if state.current_domain is None or is_new_stroke or inversion_domain != state.current_domain:
                # Set the current inversion domain to the new one
                state.current_domain = inversion_domain
                state.theory_symbols_in_current_domain = [()]
                state.first_key_index_in_current_domain = key_index
            
            state.theory_symbols_in_current_domain.append(results)

            for result in results:
                for results_chain in state.paths_ending_with(result):
                    if len(results_chain) == 1: continue

                    
                    if any(len(chain_result.theory_symbol_result.theory_symbols) != 1 for chain_result in results_chain):
                        continue # TODO handle clusters

                    theory_symbols = tuple(chain_result.theory_symbol_result.theory_symbols[0] for chain_result in results_chain)

                    chord = sum((chain_result.theory_symbol_result.chord for chain_result in results_chain), Stroke.from_integer(0))

                    yield ChordToTheorySymbolSearchResultWithSrcIndex(
                        ChordToTheorySymbolSearchResult(
                            (create_inversion_theory_symbol(theory_symbols),),
                            chord,
                        ),
                        results_chain[0].chord_start_key_index,
                    )

        return None

    return plugin
