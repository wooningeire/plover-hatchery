from typing import Iterable

from plover.steno import Stroke

from ..sopheme.Sound import Sound
from ..stenophoneme.Stenophoneme import vowel_phonemes
from ..sopheme.Steneme import Steneme
from ..theory.theory import amphitheory
from .build_trie.state import ConsonantVowelGroup, OutlineSounds

def get_outline_phonemes(outline: Iterable[Stroke]):
    consonant_vowel_groups: list[ConsonantVowelGroup] = []

    current_group_consonants: list[Sound] = []
    
    for stroke in outline:
        left_bank_consonants, vowels, right_bank_consonants, asterisk = amphitheory.split_stroke_parts(stroke)
        if len(asterisk) > 0:
            return None

        current_group_consonants.extend(Sound(phoneme, None) for phoneme in amphitheory.split_consonant_phonemes(left_bank_consonants))

        if len(vowels) > 0:
            is_diphthong_transition = len(consonant_vowel_groups) > 0 and len(current_group_consonants) == 0
            if is_diphthong_transition and (prev_vowel := consonant_vowel_groups[-1].vowel).phoneme in amphitheory.spec.DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL:
                current_group_consonants.append(Sound(amphitheory.spec.DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL[prev_vowel.phoneme], None))

            consonant_vowel_groups.append(ConsonantVowelGroup(tuple(current_group_consonants), Sound(amphitheory.chords_to_phonemes_vowels[vowels], None)))

            current_group_consonants = []

        current_group_consonants.extend(Sound(phoneme, None) for phoneme in amphitheory.split_consonant_phonemes(right_bank_consonants))

    return OutlineSounds(tuple(consonant_vowel_groups), tuple(current_group_consonants))


class OutlineSoundsBuilder:
    def __init__(self):
        self.__consonant_vowel_groups: list[ConsonantVowelGroup] = []
        self.__current_group_consonants: list[Sound] = []


    @property
    def __last_sound_was_vowel(self):
        return len(self.__consonant_vowel_groups) > 0 and len(self.__current_group_consonants) == 0


    def append_diphthong_transition(self):
        if not self.__last_sound_was_vowel: return
        
        prev_vowel = self.__consonant_vowel_groups[-1].vowel
        if prev_vowel.phoneme not in amphitheory.spec.DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL: return

        self.__current_group_consonants.append(Sound(amphitheory.spec.DIPHTHONG_TRANSITIONS_BY_FIRST_VOWEL[prev_vowel.phoneme], None))


    def add_consonant(self, consonant: Sound):
        self.__current_group_consonants.append(consonant)
    

    def add_vowel(self, vowel: Sound):
        self.append_diphthong_transition()

        self.__consonant_vowel_groups.append(ConsonantVowelGroup(tuple(self.__current_group_consonants), vowel))
        self.__current_group_consonants = []


    def build_sounds(self):
        return OutlineSounds(tuple(self.__consonant_vowel_groups), tuple(self.__current_group_consonants))


def get_sopheme_phonemes(sophemes: Iterable[Steneme]):
    builder = OutlineSoundsBuilder()

    for sopheme in sophemes:
        if sopheme.phoneme is None and len(sopheme.steno) == 0:
            continue


        elif sopheme.phoneme in vowel_phonemes:
            builder.add_vowel(Sound.from_sopheme(sopheme))


        elif any(any(key in stroke.rtfcre for key in "AOEU") for stroke in sopheme.steno):

            for stroke in sopheme.steno:
                vowel_substroke = stroke & Stroke.from_steno("AOEU")
                if len(vowel_substroke) > 0:
                    break
                
            vowel_phoneme = amphitheory.chords_to_phonemes_vowels[vowel_substroke]
            builder.add_vowel(Sound(vowel_phoneme, sopheme))
        
        else:
            if sopheme.phoneme is not None:
                builder.add_consonant(Sound.from_sopheme(sopheme))
            else:
                for stroke in sopheme.steno:
                    for phoneme in amphitheory.split_consonant_phonemes(stroke):
                        builder.add_consonant(Sound(phoneme, sopheme))


    return builder.build_sounds()