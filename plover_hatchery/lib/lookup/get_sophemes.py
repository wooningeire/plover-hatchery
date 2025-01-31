from typing import Iterable

from plover.steno import Stroke

from ..sophone.Sophone import vowel_phonemes
from ..sopheme import Sopheme, Keysymbol, Sound
from ..theory.theory import amphitheory
from .build_trie.state import ConsonantVowelGroup, OutlineSounds

# def get_outline_phonemes(outline: Iterable[Stroke]):
#     consonant_vowel_groups: list[ConsonantVowelGroup] = []

#     current_group_consonants: list[Sound] = []
    
#     for stroke in outline:
#         left_bank_consonants, vowels, right_bank_consonants, asterisk = amphitheory.split_stroke_parts(stroke)
#         if len(asterisk) > 0:
#             return None

#         current_group_consonants.extend(Sound(phoneme, None) for phoneme in amphitheory.split_consonant_phonemes(left_bank_consonants))

#         if len(vowels) > 0:
#             is_diphthong_transition = len(consonant_vowel_groups) > 0 and len(current_group_consonants) == 0
#             if is_diphthong_transition and (prev_vowel := consonant_vowel_groups[-1].vowel).keysymbol in amphitheory.spec.DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL:
#                 current_group_consonants.append(Sound(amphitheory.spec.DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL[prev_vowel.keysymbol], None))

#             consonant_vowel_groups.append(ConsonantVowelGroup(tuple(current_group_consonants), Sound(amphitheory.chords_to_phonemes_vowels[vowels], None)))

#             current_group_consonants = []

#         current_group_consonants.extend(Sound(phoneme, None) for phoneme in amphitheory.split_consonant_phonemes(right_bank_consonants))

#     return OutlineSounds(tuple(consonant_vowel_groups), tuple(current_group_consonants))


class _OutlineSoundsBuilder:
    def __init__(self):
        self.__consonant_vowel_groups: list[ConsonantVowelGroup] = []
        self.__current_group_consonants: list[Sound] = []


    @property
    def __last_sound_was_vowel(self):
        return len(self.__consonant_vowel_groups) > 0 and len(self.__current_group_consonants) == 0


    def __append_diphthong_transition(self):
        if not self.__last_sound_was_vowel: return
        
        prev_vowel = self.__consonant_vowel_groups[-1].vowel
        diphthong_transition_sopheme = amphitheory.spec.vowel_diphthong_transition(prev_vowel)
        if diphthong_transition_sopheme is None: return

        self.__current_group_consonants.append(Sound(diphthong_transition_sopheme.keysymbols[0], diphthong_transition_sopheme))


    def add_consonant(self, consonant: Sound):
        self.__current_group_consonants.append(consonant)
    

    def add_vowel(self, vowel: Sound):
        self.__append_diphthong_transition()

        self.__consonant_vowel_groups.append(ConsonantVowelGroup(tuple(self.__current_group_consonants), vowel))
        self.__current_group_consonants = []


    def build_sounds(self):
        return OutlineSounds(tuple(self.__consonant_vowel_groups), tuple(self.__current_group_consonants))


def get_sopheme_sounds(sophemes: Iterable[Sopheme]):
    builder = _OutlineSoundsBuilder()

    for sopheme in sophemes:
        for keysymbol in sopheme.keysymbols:
            if keysymbol.is_vowel:
                builder.add_vowel(Sound(keysymbol, sopheme))
            else:
                builder.add_consonant(Sound(keysymbol, sopheme))


    return builder.build_sounds()