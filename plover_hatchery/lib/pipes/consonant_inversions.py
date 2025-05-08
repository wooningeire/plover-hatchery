import itertools
from typing import Any, Generator


from dataclasses import dataclass, field

from plover.steno import Stroke
from plover_hatchery.lib.pipes.Plugin import define_plugin, GetPluginApi
from plover_hatchery.lib.pipes.soph_trie import ChordToSophSearchResult, ChordToSophSearchResultWithSrcIndex, LookupResultWithAssociations, SophChordAssociation, SophsToTranslationSearchPath, soph_trie
from plover_hatchery.lib.pipes.types import EntryIndex, Soph
from plover_hatchery.lib.sopheme.SophemeSeq import SophemeSeqPhoneme
from plover_hatchery.lib.trie import NondeterministicTrie, NodeSrc, JoinedTriePaths
from plover_hatchery.lib.trie.Transition import TransitionCostKey


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


        @dataclass(frozen=True)
        class PastConsonant:
            node_srcs: tuple[NodeSrc, ...]
            sophs: tuple[Soph, ...]
            phoneme: SophemeSeqPhoneme


        class ConsonantInversionsAddEntryState:
            def __init__(self):
                self.past_consonants: list[PastConsonant] = []


        @soph_trie_api.begin_add_entry.listen(consonant_inversions)
        def _(**_):
            return ConsonantInversionsAddEntryState()


        def create_inversion_soph(sophs: "tuple[Soph | None, ...]"):
            non_null_sophs = (
                soph
                for soph in sophs
                if soph is not None
            )
            sorted_sophs = sorted(non_null_sophs, key=lambda soph: soph.value)
            return Soph(f"inversion:{' '.join(soph.value for soph in sorted_sophs)}")

        def get_inversion_sophs(past_consonants: list[PastConsonant]):
            product_choices = (
                (*consonant.sophs, None) if consonant.phoneme.keysymbol.optional else consonant.sophs
                for consonant in past_consonants
            )
            for combo in itertools.product(*product_choices):
                yield create_inversion_soph(combo)


        @soph_trie_api.add_soph_transition.listen(consonant_inversions)
        def _(
            state: ConsonantInversionsAddEntryState,
            sophs: set[Soph],
            phoneme: SophemeSeqPhoneme,
            paths: JoinedTriePaths,
            node_srcs: tuple[NodeSrc, ...],
            trie: NondeterministicTrie[Soph, EntryIndex],
            entry_id: EntryIndex,
            **_,
        ):
            if any(soph not in consonant_sophs for soph in sophs):
                # TODO verify this
                if not phoneme.keysymbol.optional:
                    state.past_consonants = []
                    
                return

            current_consonant_sophs = tuple(sophs & consonant_sophs)
            if len(current_consonant_sophs) == 0: return

            state.past_consonants.append(PastConsonant(node_srcs, current_consonant_sophs, phoneme))

            if paths.dst_node_id is not None:
                for i, consonant in enumerate(state.past_consonants[:-1]):
                    inversion_sophs = get_inversion_sophs(state.past_consonants[i:])
                    _ = trie.link_join(NodeSrc.increment_costs(consonant.node_srcs, 50), paths.dst_node_id, inversion_sophs, entry_id)


            #     for consonant in state.past_consonants:
            #         new_paths = trie.join(consonant.node_srcs, sophs, entry_id)
                    
            #         for seq in new_paths.transition_seqs:
            #             soph_trie_api.register_transition(seq.transitions[0], entry_id, phoneme)

            #         if new_paths.dst_node_id is None: continue

                    
            #         loop_paths = trie.link_join((NodeSrc(new_paths.dst_node_id),), paths.dst_node_id, consonant.sophs, entry_id)
            #         return_paths = trie.link_join((NodeSrc(new_paths.dst_node_id),), new_paths.dst_node_id, consonant.sophs, entry_id)
                    
            #         for seq in loop_paths.transition_seqs:
            #             soph_trie_api.register_transition(seq.transitions[0], entry_id, consonant.phoneme)
                    
            #         for seq in return_paths.transition_seqs:
            #             soph_trie_api.register_transition(seq.transitions[0], entry_id, consonant.phoneme)




        def get_inversion_domain_of_stroke(stroke: Stroke):
            domains = tuple(filter(lambda domain: len(domain & stroke) > 0, inversion_domains))

            if len(domains) != 1:
                return None

            return domains[0]


        # @dataclass(frozen=True)
        # class DomainSophs:
        #     sophs: tuple[Soph, ...]
        #     chord_starting_key_index: int
        #     required_floaters: Stroke


        # def get_sophs_in_current_inversion_domain(path: SophsToTranslationSearchPath, consumed_keys: tuple[str, ...], stroke_starter_key_indices: set[int]):
        #     newest_chord = Stroke.from_keys(consumed_keys[path.sophs_and_chords_used[-1].chord_start_key_index:])
        #     current_domain = get_inversion_domain_of_stroke(newest_chord)
        #     print(current_domain)
        #     if current_domain is None: return None # Chord crosses domains or is not supposed to be inverted


        #     # Read backward to get all the sophs in this inversion domain
        #     prev_chord_start_key_index = path.sophs_and_chords_used[-1].chord_start_key_index
        #     sophs: list[Soph] = list(reversed(path.sophs_and_chords_used[-1].sophs))
        #     for i in range(len(path.sophs_and_chords_used) - 2, -1, -1):
        #         association = path.sophs_and_chords_used[i]
        #         chord = Stroke.from_keys(consumed_keys[association.chord_start_key_index:prev_chord_start_key_index])
        #         domain = get_inversion_domain_of_stroke(chord)
        #         print("\t", chord, domain)
        #         if domain is None or domain != current_domain: break # We're done

        #         sophs.extend(reversed(association.sophs))
        #         prev_chord_start_key_index = association.chord_start_key_index

        #         if domain in stroke_starter_key_indices: break


        #     return DomainSophs(tuple(reversed(sophs)), prev_chord_start_key_index, required_floaters)


        @dataclass
        class ConsonantInversionsLookupState:
            current_domain: "Stroke | None" = None
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




        # class Filterer:
        #     def __init__(self):
        #         self.__current_domain: "Stroke | None" = None
        #         self.__current_domain_phonemes: list[SophemeSeqPhoneme] = []

        #         self.__next_phoneme_to_validate: "SophemeSeqPhoneme | None" = None

        #     def reset(self):
        #         self.__current_domain = None
        #         self.__current_domain_phonemes = []


        #     def validate_consecutivity(self):
        #         """
        #         Ensure that all the consonants seen in the current bank occur consecutively when sorted and continue
        #         immediately from the last validated phoneme
        #         """

        #         if len(self.__current_domain_phonemes) == 0:
        #             return True

        #         if self.__current_domain is not None:
        #             phonemes_order_to_check = sorted(self.__current_domain_phonemes, key=lambda phoneme: phoneme.indices)
        #         else:
        #             phonemes_order_to_check = self.__current_domain_phonemes


        #         if self.__next_phoneme_to_validate is not None:
        #             current_phoneme = self.__next_phoneme_to_validate
        #         else:
        #             current_phoneme = phonemes_order_to_check[0].seq.first_phoneme()

        #         if current_phoneme is None:
        #             return True



        #         looking_for_phoneme_index = 0
        #         while looking_for_phoneme_index < len(phonemes_order_to_check):
        #             if current_phoneme is None:
        #                 return False

        #             if current_phoneme == phonemes_order_to_check[looking_for_phoneme_index]:
        #                 looking_for_phoneme_index += 1
        #                 current_phoneme = current_phoneme.next()
        #                 continue

        #             if current_phoneme.keysymbol.optional:
        #                 current_phoneme = current_phoneme.next()
        #                 continue

        #             return False


        #         self.__next_phoneme_to_validate = current_phoneme
        #         return True


        #     def check_association(self, association: SophChordAssociation):
        #         if association.chord_starts_new_stroke:
        #             is_valid = self.validate_and_start_new_bank()
        #             if not is_valid:
        #                 return False

        #         new_domain = get_inversion_domain_of_stroke(association.chord)
        #         if new_domain is None or self.__current_domain is None or new_domain != self.__current_domain:
        #             is_valid = self.validate_and_start_new_bank()
        #             if not is_valid:
        #                 return False

        #         self.__current_domain_phonemes.extend(association.phonemes)                
        #         self.__current_domain = new_domain

        #         return True


        #     def validate_and_start_new_bank(self):
        #         if not self.validate_consecutivity():
        #             return False
                    
        #         self.reset()
        #         return True



        #     def final_validate(self):
        #         if not self.validate_consecutivity():
        #             return False
                
        #         return self.__next_phoneme_to_validate is None


        # @soph_trie_api.validate_lookup_result.listen(consonant_inversions)
        # def _(result: LookupResultWithAssociations, trie: NondeterministicTrie[Soph, EntryIndex], **_):
        #     filtering_state = Filterer()

        #     for association in result.sophs_and_chords_used:
        #         if not filtering_state.check_association(association):
        #             return False

        #     return filtering_state.final_validate()

        return None

    return plugin