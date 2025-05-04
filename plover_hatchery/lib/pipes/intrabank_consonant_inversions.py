from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, final

from plover.steno import Stroke

from plover_hatchery.lib.config import TRIE_STROKE_BOUNDARY_KEY
from plover_hatchery.lib.pipes import key_by_key_lookup
from plover_hatchery.lib.pipes.Plugin import Plugin, GetPluginApi, define_plugin
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.declare_banks import declare_banks
from plover_hatchery.lib.pipes.join import JoinedTriePaths, NodeSrc, join_on_strokes, link_join_on_strokes
from plover_hatchery.lib.pipes.lookup_result_filter import lookup_result_filter
from plover_hatchery.lib.sopheme import SophemeSeq
from plover_hatchery.lib.sopheme.SophemeSeq import SophemeSeqPhoneme
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie, TriePath
from plover_hatchery.lib.trie.Transition import TransitionCostInfo, TransitionCostKey, TransitionKey
from .banks import BanksState, banks


def intrabank_consonant_inversions() -> Plugin[None]:
    @define_plugin(intrabank_consonant_inversions)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_):
        banks_info = get_plugin_api(declare_banks)
        banks_api = get_plugin_api(banks)
        filtering_api = get_plugin_api(lookup_result_filter)
        lookup_api = get_plugin_api(key_by_key_lookup)

        """
        

        Idea (SLOW LOOKUP): For each past consonant source node, create a link ("skip transition") from it to the newest consonant destination node with the current phoneme.
        Then create a loop ("loop transition") from the destination node to itself for each of the past consonant phonemes.

        Idea (SLOWER LOOKUP): For each consonant source node, create a loop from it to itself for each consonant chord thereafter.
        Replace the original consonant transitions with epsilon ("pass") transitions that may only be traversed
        if that consonant has been traversed in a previous node's loop.
        """


        @final
        @dataclass
        class ConsonantInversionsState:
            inversion_branch_left_src_nodes: list[NodeSrc] = field(default_factory=list)
            inversion_branch_right_src_nodes: list[NodeSrc] = field(default_factory=list)
            past_phonemes: list[SophemeSeqPhoneme] = field(default_factory=list)


        @final
        @dataclass
        class GlobalState:
            transitions_to_phonemes: dict[TransitionCostKey, SophemeSeqPhoneme] = field(default_factory=dict)

            # pass_transitions_to_satisfying_loop_transitions: dict[TransitionKey, set[TransitionKey]] = field(default_factory=lambda: defaultdict(set))
            # loop_transitions_to_similar_loop_transitions: dict[TransitionKey, set[TransitionKey]] = field(default_factory=lambda: defaultdict(set))

        global_state: GlobalState

        @base_hooks.begin_build_lookup.listen(intrabank_consonant_inversions)
        def _(**_):
            nonlocal global_state
            global_state = GlobalState()

        
        @banks_api.begin.listen(intrabank_consonant_inversions)
        def _(**_):
            return ConsonantInversionsState()


        @banks_api.before_complete_consonant.listen(intrabank_consonant_inversions)
        def _(state: ConsonantInversionsState, banks_state: BanksState, left_node: "int | None", right_node: "int | None", left_paths: JoinedTriePaths, right_paths: JoinedTriePaths, **_):
            if banks_state.current_phoneme is None: return


            inversion_branch_left_paths = join_on_strokes(banks_state.trie, state.inversion_branch_left_src_nodes, banks_api.left_chords(banks_state.current_phoneme), banks_state.entry_id)
            inversion_branch_right_paths = join_on_strokes(banks_state.trie, state.inversion_branch_right_src_nodes, banks_api.right_chords(banks_state.current_phoneme), banks_state.entry_id)

            for seq in inversion_branch_left_paths.transition_seqs:
                global_state.transitions_to_phonemes[TransitionCostKey(seq.transitions[0], banks_state.entry_id)] = banks_state.current_phoneme
            for seq in inversion_branch_right_paths.transition_seqs:
                global_state.transitions_to_phonemes[TransitionCostKey(seq.transitions[0], banks_state.entry_id)] = banks_state.current_phoneme



            left_inversion_branch_node = inversion_branch_left_paths.dst_node_id
            right_inversion_branch_node = inversion_branch_right_paths.dst_node_id

            for phoneme in state.past_phonemes:
                if left_inversion_branch_node is not None:
                    for chord in banks_api.left_chords(phoneme):
                        transitions = banks_state.trie.link_chain(left_inversion_branch_node, left_inversion_branch_node, chord.keys(), TransitionCostInfo(50, banks_state.entry_id))
                        global_state.transitions_to_phonemes[TransitionCostKey(transitions[0], banks_state.entry_id)] = phoneme
                        
                        if left_node is not None:
                            transitions = banks_state.trie.link_chain(left_inversion_branch_node, left_node, chord.keys(), TransitionCostInfo(50, banks_state.entry_id))
                            global_state.transitions_to_phonemes[TransitionCostKey(transitions[0], banks_state.entry_id)] = phoneme

                if right_inversion_branch_node is not None:
                    for chord in banks_api.right_chords(phoneme):
                        transitions = banks_state.trie.link_chain(right_inversion_branch_node, right_inversion_branch_node, chord.keys(), TransitionCostInfo(50, banks_state.entry_id))
                        global_state.transitions_to_phonemes[TransitionCostKey(transitions[0], banks_state.entry_id)] = phoneme
                        
                        if right_node is not None:
                            transitions = banks_state.trie.link_chain(right_inversion_branch_node, right_node, chord.keys(), TransitionCostInfo(50, banks_state.entry_id))
                            global_state.transitions_to_phonemes[TransitionCostKey(transitions[0], banks_state.entry_id)] = phoneme



            # for node_data in state.nodes:
            #     if left_node is not None:
            #         # Create skip transition
            #         paths = link_join_on_strokes(banks_state.trie, node_data.left_srcs, left_node, banks_api.left_chords(banks_state.current_phoneme), banks_state.entry_id)
            #         for seq in paths.transition_seqs:
            #             global_state.transitions_to_phonemes[TransitionCostKey(seq.transitions[0], banks_state.entry_id)] = banks_state.current_phoneme

            #         # Create loop transition
            #         for chord in banks_api.left_chords(node_data.phoneme):
            #             transitions = banks_state.trie.link_chain(left_node, left_node, chord.keys(), TransitionCostInfo(50, banks_state.entry_id))
            #             global_state.transitions_to_phonemes[TransitionCostKey(transitions[0], banks_state.entry_id)] = node_data.phoneme


            #     if right_node is not None:
            #         # Create skip transition
            #         paths = link_join_on_strokes(banks_state.trie, node_data.right_srcs, right_node, banks_api.right_chords(banks_state.current_phoneme), banks_state.entry_id)
            #         for seq in paths.transition_seqs:
            #             global_state.transitions_to_phonemes[TransitionCostKey(seq.transitions[0], banks_state.entry_id)] = banks_state.current_phoneme
                
            #         # Create loop transition
            #         for chord in banks_api.right_chords(node_data.phoneme):
            #             transitions = banks_state.trie.link_chain(right_node, right_node, chord.keys(), TransitionCostInfo(50, banks_state.entry_id))
            #             global_state.transitions_to_phonemes[TransitionCostKey(transitions[0], banks_state.entry_id)] = node_data.phoneme
                


            state.past_phonemes.append(banks_state.current_phoneme)
            state.inversion_branch_left_src_nodes.extend(banks_state.left_srcs)
            state.inversion_branch_right_src_nodes.extend(banks_state.right_srcs)

            if left_inversion_branch_node is not None:
                state.inversion_branch_left_src_nodes.append(NodeSrc(left_inversion_branch_node))

            if right_inversion_branch_node is not None:
                state.inversion_branch_right_src_nodes.append(NodeSrc(right_inversion_branch_node))


            # The transitions from the banks plugin serve as skip transitions
            for seq in left_paths.transition_seqs:
                global_state.transitions_to_phonemes[TransitionCostKey(seq.transitions[0], banks_state.entry_id)] = banks_state.current_phoneme
            for seq in right_paths.transition_seqs:
                global_state.transitions_to_phonemes[TransitionCostKey(seq.transitions[0], banks_state.entry_id)] = banks_state.current_phoneme

            # satisfying_loop_transitions: set[TransitionKey] = set()

            # for node_data in state.nodes:
            #     for src in node_data.left_srcs:
            #         cost = src.cost
            #         if node_data.phoneme != banks_state.current_phoneme:
            #             cost += 50


            #         for chord in banks_api.left_chords(banks_state.current_phoneme):
            #             left_transitions = banks_state.trie.link_chain(src.node, src.node, chord.keys(), TransitionCostInfo(cost, banks_state.entry_id))

            #             global_state.loop_transitions_to_phonemes[TransitionCostKey(left_transitions[0], banks_state.entry_id)] = banks_state.current_phoneme
            #             satisfying_loop_transitions.add(left_transitions[0])
            #             global_state.loop_transitions_to_similar_loop_transitions[left_transitions[0]] = satisfying_loop_transitions

            #     for src in node_data.right_srcs:
            #         cost = src.cost
            #         if node_data.phoneme != banks_state.current_phoneme:
            #             cost += 50


            #         for chord in banks_api.right_chords(banks_state.current_phoneme):
            #             right_transitions = banks_state.trie.link_chain(src.node, src.node, chord.keys(), TransitionCostInfo(cost, banks_state.entry_id))

            #             global_state.loop_transitions_to_phonemes[TransitionCostKey(right_transitions[0], banks_state.entry_id)] = banks_state.current_phoneme
            #             satisfying_loop_transitions.add(right_transitions[0])
            #             global_state.loop_transitions_to_similar_loop_transitions[right_transitions[0]] = satisfying_loop_transitions


            # if left_node is not None:
            #     for src in banks_state.left_srcs:
            #         transition = banks_state.trie.link(src.node, left_node, None, TransitionCostInfo(src.cost, banks_state.entry_id))

            #         global_state.pass_transitions_to_phonemes[TransitionCostKey(transition, banks_state.entry_id)] = banks_state.current_phoneme
            #         global_state.pass_transitions_to_satisfying_loop_transitions[transition] |= satisfying_loop_transitions

            # if right_node is not None:
            #     for src in banks_state.right_srcs:
            #         transition = banks_state.trie.link(src.node, right_node, None, TransitionCostInfo(src.cost, banks_state.entry_id))

            #         global_state.pass_transitions_to_phonemes[TransitionCostKey(transition, banks_state.entry_id)] = banks_state.current_phoneme
            #         global_state.pass_transitions_to_satisfying_loop_transitions[transition] |= satisfying_loop_transitions

            
            # for transition in satisfying_loop_transitions:
            #     global_state.loop_transitions_to_similar_loop_transitions[transition] |= satisfying_loop_transitions



        @banks_api.before_complete_vowel.listen(intrabank_consonant_inversions)
        def _(state: ConsonantInversionsState, banks_state: BanksState, **_):
            if banks_state.current_phoneme is not None and banks_state.current_phoneme.keysymbol.optional: return
            state.inversion_branch_left_src_nodes = []
            state.inversion_branch_right_src_nodes = []
            state.past_phonemes = []


        # def check_pass_is_allowed(trie: NondeterministicTrie[str, int], existing_trie_path: TriePath, new_transition: TransitionKey):
        #     if new_transition not in global_state.pass_transitions_to_satisfying_loop_transitions: return True

        #     loop_transitions = global_state.pass_transitions_to_satisfying_loop_transitions[new_transition]

        #     for transition in reversed(existing_trie_path.transitions):
        #         if transition.key_id is not None and trie.get_key(transition.key_id) == TRIE_STROKE_BOUNDARY_KEY:
        #             break

        #         if transition in loop_transitions:
        #             return True

        #     return False
        

        # def check_loop_is_not_repeated(existing_trie_path: TriePath, new_transition: TransitionKey):
        #     if new_transition not in global_state.loop_transitions_to_similar_loop_transitions: return True

        #     similar_loop_transitions = global_state.loop_transitions_to_similar_loop_transitions[new_transition]

        #     for transition in existing_trie_path.transitions:
        #         if transition in similar_loop_transitions:
        #             return False

        #     return True


        # @lookup_api.check_traverse.listen(intrabank_consonant_inversions)
        # def _(trie: NondeterministicTrie[str, int], existing_trie_path: TriePath, new_transition: TransitionKey, **_):
        #     return (
        #         check_pass_is_allowed(trie, existing_trie_path, new_transition)
        #         and check_loop_is_not_repeated(existing_trie_path, new_transition)
        #     )

        @final
        @dataclass
        class Filterer:
            def __init__(self):
                self.__current_bank_stroke: Stroke = Stroke.from_integer(0)
                self.__current_bank_phonemes: list[SophemeSeqPhoneme] = []

                self.__next_phoneme_to_validate: "SophemeSeqPhoneme | None" = None

            def add_to_stroke(self, stroke: Stroke):
                if len(stroke & banks_info.mid) == 0:
                    self.__current_bank_stroke += stroke

            @property
            def is_left_bank(self):
                return len(self.__current_bank_stroke & banks_info.left) > 0

            @property
            def is_right_bank(self):
                return len(self.__current_bank_stroke & banks_info.right) > 0

            def reset(self):
                self.__current_bank_stroke = Stroke.from_integer(0)
                self.__current_bank_phonemes = []


            def validate_consecutivity(self):
                """
                Ensure that all the consonants seen in the current bank occur consecutively when sorted and continue
                immediately from the last validated phoneme
                """

                if len(self.__current_bank_phonemes) == 0:
                    return True

                sorted_phonemes = sorted(self.__current_bank_phonemes, key=lambda phoneme: phoneme.indices)


                if self.__next_phoneme_to_validate is not None:
                    current_phoneme = self.__next_phoneme_to_validate
                else:
                    current_phoneme = sorted_phonemes[0].seq.first_consonant()

                if current_phoneme is None:
                    return True



                looking_for_phoneme_index = 0
                while looking_for_phoneme_index < len(sorted_phonemes):
                    if current_phoneme is None:
                        return False

                    if current_phoneme == sorted_phonemes[looking_for_phoneme_index]:
                        looking_for_phoneme_index += 1
                        current_phoneme = current_phoneme.next_consonant()
                        continue

                    if current_phoneme.keysymbol.optional:
                        current_phoneme = current_phoneme.next_consonant()
                        continue

                    return False


                self.__next_phoneme_to_validate = current_phoneme
                return True


            def check_transition(self, cost_key: TransitionCostKey, trie: NondeterministicTrie[str, int]):
                if cost_key.transition.key_id is None: return True

                key = trie.get_key(cost_key.transition.key_id)

                if key == TRIE_STROKE_BOUNDARY_KEY:
                    return self.validate_and_start_new_bank()

                key_stroke = Stroke.from_keys((key,))
                if self.is_left_bank and len(key_stroke & ~banks_info.left) > 0:
                    return self.validate_and_start_new_bank()

                phoneme = global_state.transitions_to_phonemes.get(cost_key)
                if phoneme is not None:
                    self.__current_bank_phonemes.append(phoneme)
                
                self.add_to_stroke(key_stroke)

                return True


            def validate_and_start_new_bank(self):
                if not self.validate_consecutivity():
                    return False
                    
                self.reset()
                return True



            def final_validate(self):
                if not self.validate_consecutivity():
                    return False
                
                return self.__next_phoneme_to_validate is None


        @filtering_api.check_should_keep.listen(intrabank_consonant_inversions)
        def _(lookup_result: LookupResult[int], trie: NondeterministicTrie[str, int], **_):
            filtering_state = Filterer()

            for transition in lookup_result.transitions:
                if not filtering_state.check_transition(TransitionCostKey(transition, lookup_result.translation_id), trie):
                    return False

            return filtering_state.final_validate()


        return None


    return plugin