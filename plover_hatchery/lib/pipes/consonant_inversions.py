import itertools
from typing import Any, Generator


from dataclasses import dataclass, field

from plover.steno import Stroke
from plover_hatchery_lib_rs import DefViewCursor, DefViewItem
from plover_hatchery.lib.pipes.Plugin import define_plugin, GetPluginApi
from plover_hatchery.lib.pipes.soph_trie import ChordToSophSearchResult, ChordToSophSearchResultWithSrcIndex, LookupResultWithAssociations, SophChordAssociation, SophsToTranslationSearchPath, soph_trie
from plover_hatchery_lib_rs import Soph, TransitionFlagManager
from plover_hatchery.lib.trie import NondeterministicTrie, TransitionSourceNode, JoinedTriePaths, TransitionFlag, TransitionCostKey



def consonant_inversions(*, consonant_sophs_str: str, inversion_domains_steno: str):
    consonant_sophs = set(Soph(value) for value in consonant_sophs_str.split())
    inversion_domains: tuple[Stroke, ...] = tuple(
        sorted(
            Stroke.from_steno(domain_steno) for domain_steno in inversion_domains_steno.split()
        )
    )

    @define_plugin(consonant_inversions)
    def plugin(get_plugin_api: GetPluginApi, **_):
        soph_trie_api = get_plugin_api(soph_trie)

        inversion_flag = soph_trie_api.transition_flags.new_flag("inversion")


        @dataclass(frozen=True)
        class PastConsonant:
            node_srcs: tuple[TransitionSourceNode, ...]
            sophs: tuple[Soph, ...]
            cursor: DefViewCursor


        class ConsonantInversionsAddEntryState:
            def __init__(self):
                self.past_consonants: list[PastConsonant] = []


        @soph_trie_api.begin_add_entry.listen(consonant_inversions)
        def _(**_):
            return ConsonantInversionsAddEntryState()


        def create_inversion_soph(sophs: "tuple[Soph, ...]"):
            sorted_sophs = sorted(sophs, key=lambda soph: soph.value)
            return Soph(f"inversion:{' '.join(soph.value for soph in sorted_sophs)}")

        def get_inversion_sophs(past_consonants: list[PastConsonant]):
            def get_product_choices():
                for consonant in past_consonants:
                    keysymbol = consonant.cursor.tip().keysymbol()

                    if keysymbol.optional:
                        yield (*consonant.sophs, None)
                    else:
                        yield consonant.sophs

            for combo in itertools.product(*get_product_choices()):
                non_null_sophs = tuple(
                    soph
                    for soph in combo
                    if soph is not None
                )
                if len(non_null_sophs) <= 1: continue

                yield create_inversion_soph(non_null_sophs)


        @soph_trie_api.add_soph_transition.listen(consonant_inversions)
        def _(
            state: ConsonantInversionsAddEntryState,
            sophs: set[Soph],
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

            if any(soph not in consonant_sophs for soph in sophs):
                keysymbol = cursor.tip().keysymbol()

                # TODO verify this
                if not keysymbol.optional:
                    state.past_consonants = []
                    
                return

            current_consonant_sophs = tuple(sophs & consonant_sophs)
            if len(current_consonant_sophs) == 0: return

            state.past_consonants.append(PastConsonant(node_srcs, current_consonant_sophs, cursor))

            if paths.dst_node_id is not None:
                for i, consonant in enumerate(state.past_consonants[:-1]):
                    inversion_sophs = get_inversion_sophs(state.past_consonants[i:])
                    new_paths = trie.link_join(
                        tuple(TransitionSourceNode.increment_costs(consonant.node_srcs, 50)),
                        paths.dst_node_id,
                        soph_trie_api.key_id_manager.get_key_ids_else_create(inversion_sophs),
                        entry_id
                    )

                    for transition_seq in new_paths.transition_seqs:
                        for transition in transition_seq.transitions:
                            soph_trie_api.transition_flags.flag_transition(TransitionCostKey(transition, entry_id), inversion_flag)




        def get_inversion_domain_of_stroke(stroke: Stroke):
            domains = tuple(filter(lambda domain: len(domain & stroke) > 0, inversion_domains))

            if len(domains) != 1:
                return None

            return domains[0]


        @dataclass
        class ConsonantInversionsLookupState:
            current_domain: Stroke | None = None
            sophs_in_current_domain: list[tuple[ChordToSophSearchResultWithSrcIndex, ...]] = field(default_factory=list)
            first_key_index_in_current_domain: int = -1

            def paths_ending_with(self, result: ChordToSophSearchResultWithSrcIndex, current_chain: tuple[ChordToSophSearchResultWithSrcIndex, ...]=()) -> Generator[tuple[ChordToSophSearchResultWithSrcIndex, ...], None, None]:
                if result.chord_start_key_index < self.first_key_index_in_current_domain:
                    return

                if result.chord_start_key_index == self.first_key_index_in_current_domain:
                    yield (result, *current_chain)

                for old_result in self.sophs_in_current_domain[result.chord_start_key_index - self.first_key_index_in_current_domain]:
                    if old_result in current_chain or old_result == result: continue

                    yield from self.paths_ending_with(old_result, (result, *current_chain))


        @soph_trie_api.begin_lookup.listen(consonant_inversions)
        def _(**_):
            return ConsonantInversionsLookupState()


        @soph_trie_api.consume_key.listen(consonant_inversions)
        def _(state: ConsonantInversionsLookupState, key: str, key_index: int, is_new_stroke: bool, results: tuple[ChordToSophSearchResultWithSrcIndex, ...], **_):
            inversion_domain = get_inversion_domain_of_stroke(Stroke.from_keys((key,)))
            if inversion_domain is None:
                # Nullify the state's inversion domain
                state.current_domain = None
                state.sophs_in_current_domain = []
                state.first_key_index_in_current_domain = -1
                return

            if state.current_domain is None or is_new_stroke or inversion_domain != state.current_domain:
                # Set the current inversion domain to the new one
                state.current_domain = inversion_domain
                state.sophs_in_current_domain = [()]
                state.first_key_index_in_current_domain = key_index
            
            state.sophs_in_current_domain.append(results)

            for result in results:
                for results_chain in state.paths_ending_with(result):
                    if len(results_chain) == 1: continue

                    
                    if any(len(chain_result.soph_result.sophs) != 1 for chain_result in results_chain):
                        continue # TODO handle clusters

                    sophs = tuple(chain_result.soph_result.sophs[0] for chain_result in results_chain)

                    chord = sum((chain_result.soph_result.chord for chain_result in results_chain), Stroke.from_integer(0))

                    yield ChordToSophSearchResultWithSrcIndex(
                        ChordToSophSearchResult(
                            (create_inversion_soph(sophs),),
                            chord,
                        ),
                        results_chain[0].chord_start_key_index,
                    )

        return None

    return plugin