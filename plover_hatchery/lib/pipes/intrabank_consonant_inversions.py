from dataclasses import dataclass, field
from typing import Any, final

from plover.steno import Stroke

from plover_hatchery.lib.config import TRIE_STROKE_BOUNDARY_KEY
from plover_hatchery.lib.pipes.Plugin import Plugin, GetPluginApi, define_plugin
from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.declare_banks import declare_banks
from plover_hatchery.lib.pipes.join import NodeSrc, join_on_strokes, link_join_on_strokes
from plover_hatchery.lib.pipes.lookup_result_filtering import lookup_result_filtering
from plover_hatchery.lib.sopheme import SophemeSeq
from plover_hatchery.lib.sopheme.SophemeSeq import SophemeSeqPhoneme
from plover_hatchery.lib.trie import LookupResult, NondeterministicTrie, TriePath
from plover_hatchery.lib.trie.Transition import TransitionCostInfo, TransitionKey
from .banks import BanksState, banks


def intrabank_consonant_inversions() -> Plugin[None]:
    @define_plugin(intrabank_consonant_inversions)
    def plugin(get_plugin_api: GetPluginApi, base_hooks: TheoryHooks, **_):
        banks_info = get_plugin_api(declare_banks)
        banks_api = get_plugin_api(banks)
        filtering_api = get_plugin_api(lookup_result_filtering)

        """
        Idea: For each consonant source node, create a loop from it to itself for each consonant chord thereafter.
        Replace the original consonant transitions with epsilon ("pass") transitions that may only be traversed
        if that consonant has been traversed in a previous node's loop.
        """


        @final
        @dataclass(frozen=True)
        class PhonemeNodes:
            phoneme: SophemeSeqPhoneme
            left_srcs: tuple[NodeSrc, ...]
            right_srcs: tuple[NodeSrc, ...]

        @final
        @dataclass
        class ConsonantInversionsState:
            nodes: list[PhonemeNodes] = field(default_factory=list)


        @final
        @dataclass
        class GlobalState:
            loop_transitions_to_phonemes: dict[TransitionKey, SophemeSeqPhoneme] = field(default_factory=dict)
            pass_transitions_to_phonemes: dict[TransitionKey, SophemeSeqPhoneme] = field(default_factory=dict)

        global_state: GlobalState

        @base_hooks.build_lookup.listen(intrabank_consonant_inversions)
        def _(**_):
            nonlocal global_state
            global_state = GlobalState()

        
        @banks_api.begin.listen(intrabank_consonant_inversions)
        def _(**_):
            return ConsonantInversionsState()


        @banks_api.before_complete_consonant.listen(intrabank_consonant_inversions)
        def _(state: ConsonantInversionsState, banks_state: BanksState, left_node: "int | None", right_node: "int | None", **_):
            if banks_state.current_phoneme is None: return


            state.nodes.append(PhonemeNodes(banks_state.current_phoneme, banks_state.left_srcs, banks_state.right_srcs))


            for node_data in state.nodes:
                for src in node_data.left_srcs:
                    for chord in banks_api.left_chords(banks_state.current_phoneme):
                        left_transitions = banks_state.trie.link_chain(src.node, src.node, chord.keys(), TransitionCostInfo(50, banks_state.entry_id))
                        global_state.loop_transitions_to_phonemes[left_transitions[0]] = banks_state.current_phoneme

                for src in node_data.right_srcs:
                    for chord in banks_api.right_chords(banks_state.current_phoneme):
                        right_transitions = banks_state.trie.link_chain(src.node, src.node, chord.keys(), TransitionCostInfo(50, banks_state.entry_id))
                        global_state.loop_transitions_to_phonemes[right_transitions[0]] = banks_state.current_phoneme


            if left_node is not None:
                for src in banks_state.left_srcs:
                    transition = banks_state.trie.link(src.node, left_node, None, TransitionCostInfo(src.cost, banks_state.entry_id))
                    global_state.pass_transitions_to_phonemes[transition] = banks_state.current_phoneme

            if right_node is not None:
                for src in banks_state.right_srcs:
                    transition = banks_state.trie.link(src.node, right_node, None, TransitionCostInfo(src.cost, banks_state.entry_id))
                    global_state.pass_transitions_to_phonemes[transition] = banks_state.current_phoneme



        @banks_api.before_complete_vowel.listen(intrabank_consonant_inversions)
        def _(state: ConsonantInversionsState, banks_state: BanksState, **_):
            if banks_state.current_phoneme is not None and banks_state.current_phoneme.keysymbol.optional: return
            state.nodes = []


        @final
        @dataclass
        class Filterer:
            def __init__(self):
                self.__current_bank_stroke: Stroke = Stroke.from_integer(0)
                self.__current_bank_phonemes: list[SophemeSeqPhoneme] = []
                self.__all_seen_phonemes: set[SophemeSeqPhoneme] = set()

                self.__last_validated_phoneme: "SophemeSeqPhoneme | None" = None

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
                Ensure that all the consonants seen in the current bank occur are consecutive when sorted and continue
                immediately from the last validated phoneme
                """

                if len(self.__current_bank_phonemes) == 0:
                    return True

                sorted_phonemes = sorted(self.__current_bank_phonemes, key=lambda phoneme: phoneme.indices)


                if self.__last_validated_phoneme is not None:
                    current_phoneme = self.__last_validated_phoneme.next_consonant()
                else:
                    current_phoneme = sorted_phonemes[0].seq.first_consonant()

                if current_phoneme is None:
                    return True



                looking_for_phoneme_index = 0
                while looking_for_phoneme_index < len(self.__current_bank_phonemes):
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


                self.__last_validated_phoneme = current_phoneme
                return True


            def check_transition(self, transition: TransitionKey, trie: NondeterministicTrie[str, int]):
                if transition.key_id is None:
                    phoneme = global_state.pass_transitions_to_phonemes.get(transition)
                    if phoneme is not None and phoneme not in self.__all_seen_phonemes:
                        return False

                else:
                    key = trie.get_key(transition.key_id)

                    if key == TRIE_STROKE_BOUNDARY_KEY:
                        return self.validate_and_start_new_bank()

                    key_stroke = Stroke.from_keys((key,))
                    if self.is_left_bank and len(key_stroke & ~banks_info.left) > 0:
                        return self.validate_and_start_new_bank()

                    phoneme = global_state.loop_transitions_to_phonemes.get(transition)
                    if phoneme is not None:
                        # print("hit phoneme", phoneme)
                        self.__current_bank_phonemes.append(phoneme)
                        self.__all_seen_phonemes.add(phoneme)
                    
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
                
                return self.__last_validated_phoneme is None


        @filtering_api.determine_should_keep.listen(intrabank_consonant_inversions)
        def _(lookup_result: LookupResult[int], trie: NondeterministicTrie[str, int], **_):
            filtering_state = Filterer()

            # print("checking")
            for transition in lookup_result.transitions:
                if not filtering_state.check_transition(transition, trie):
                    return False

            return filtering_state.final_validate()


        return None


    return plugin