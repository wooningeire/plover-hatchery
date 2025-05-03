from typing import Callable
from collections.abc import Iterable

from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.pipes.consonants_vowels_enumeration import consonants_vowels_enumeration
from plover_hatchery.lib.sopheme import Keysymbol, SophemeSeq, SophemeSeqPhoneme

from ..sopheme import Sopheme
from .Plugin import GetPluginApi, Plugin, define_plugin

    # class _OutlineSoundsBuilder:
    #     def __init__(self):
    #         self.__consonant_vowel_groups: list[ConsonantVowelGroup] = []
    #         self.__current_group_consonants: list[Sound] = []


    #     @property
    #     def __last_sound_was_vowel(self):
    #         return len(self.__consonant_vowel_groups) > 0 and len(self.__current_group_consonants) == 0


    #     def __append_diphthong_transition(self):
    #         if not self.__last_sound_was_vowel: return
            
    #         prev_vowel = self.__consonant_vowel_groups[-1].vowel
    #         diphthong_transition_sophemes = vowel_diphthong_transition(prev_vowel)
    #         for sopheme in diphthong_transition_sophemes:
    #             self.__current_group_consonants.append(Sound(sopheme.keysymbols[0], sopheme))
    #             break
    #             # TODO


    #     def add_consonant(self, consonant: SophemeSeqEntry):
    #         self.__current_group_consonants.append(consonant)
        

    #     def add_vowel(self, vowel: SophemeSeqEntry):
    #         self.__append_diphthong_transition()

    #         self.__consonant_vowel_groups.append(ConsonantVowelGroup(tuple(self.__current_group_consonants), vowel))
    #         self.__current_group_consonants = []


    #     def build_sounds(self):
    #         return OutlineSounds(tuple(self.__consonant_vowel_groups), tuple(self.__current_group_consonants))


    # def get_sopheme_sounds(sophemes: Iterable[Sopheme]):
    #     builder = _OutlineSoundsBuilder()

    #     for sopheme in sophemes:
    #         for keysymbol in sopheme.keysymbols:
    #             if keysymbol.is_vowel:
    #                 builder.add_vowel(Sound(keysymbol, sopheme))
    #             else:
    #                 builder.add_consonant(Sound(keysymbol, sopheme))


    #     return builder.build_sounds()

def diphthong_transition_consonants(
    *,
    keysymbols_by_first_vowel: Callable[[SophemeSeqPhoneme], Iterable[Sopheme]],
) -> Plugin[None]:
        @define_plugin(diphthong_transition_consonants)
        def plugin(base_hooks: TheoryHooks, **_):
            @base_hooks.process_sopheme_seq.listen(diphthong_transition_consonants)
            def _(sopheme_seq: SophemeSeq, **_):
                prev_phoneme_if_was_vowel = None

                for sopheme, phonemes in sopheme_seq.phonemes_by_sopheme():
                    keysymbols: list[Keysymbol] = []

                    for phoneme in phonemes:
                        if phoneme.keysymbol.is_vowel:
                            if prev_phoneme_if_was_vowel:
                                # Add the diphthong transition consonant
                                diphthong_transition_sophemes = keysymbols_by_first_vowel(prev_phoneme_if_was_vowel)
                                for sopheme in diphthong_transition_sophemes:
                                    keysymbols.extend(sopheme.keysymbols)
                                    break
                                    # TODO multiple options
                            
                            keysymbols.append(phoneme.keysymbol)

                            prev_phoneme_if_was_vowel = phoneme


                        else:
                            keysymbols.append(phoneme.keysymbol)

                            prev_phoneme_if_was_vowel = None

                    yield Sopheme(sopheme.chars, tuple(keysymbols))


            return None

        
        return plugin