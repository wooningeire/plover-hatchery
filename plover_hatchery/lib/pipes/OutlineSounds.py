from tokenize import group
from typing import NamedTuple
from dataclasses import dataclass, field
import dataclasses

from ..trie import NondeterministicTrie
from ..sopheme.Sound import Sound

class ConsonantVowelGroup(NamedTuple):
    consonants: tuple[Sound, ...]
    vowel: Sound

@dataclass(frozen=True)
class OutlineSounds:
    nonfinals: tuple[ConsonantVowelGroup, ...]
    final_consonants: tuple[Sound, ...]

    def get_consonants(self, group_index: int):
        if group_index == len(self.nonfinals):
            return self.final_consonants
        return self.nonfinals[group_index].consonants

    def get_consonant(self, group_index: int, phoneme_index: int):
        return self.get_consonants(group_index)[phoneme_index]

    def __getitem__(self, key: tuple[int, int]):
        group_index, phoneme_index = key

        if self.is_last_group(group_index):
            return self.final_consonants[phoneme_index]
        if phoneme_index == len(self.nonfinals[group_index].consonants):
            return self.nonfinals[group_index].vowel
        return self.nonfinals[group_index].consonants[phoneme_index]
    
    def decrement_consonant_index(self, group_index: int, phoneme_index: int):
        current_consonants = self.get_consonants(group_index)

        phoneme_index -= 1

        while phoneme_index == -1:
            if group_index == 0:
                return None
        
            group_index -= 1
            current_consonants = self.get_consonants(group_index)
            phoneme_index = len(current_consonants) - 1

        return group_index, phoneme_index
    
    def increment_consonant_index(self, group_index: int, phoneme_index: int):
        current_consonants = self.get_consonants(group_index)

        phoneme_index += 1

        while phoneme_index == len(current_consonants):
            if group_index == len(self.nonfinals):
                return None
        
            group_index += 1
            phoneme_index = 0
            current_consonants = self.get_consonants(group_index)

        return group_index, phoneme_index
    
    def increment_index(self, group_index: int, phoneme_index: int):
        current_consonants = self.get_consonants(group_index)

        phoneme_index += 1

        if group_index == len(self.nonfinals) and phoneme_index >= len(current_consonants):
            return None

        if group_index < len(self.nonfinals) and phoneme_index > len(current_consonants):
            group_index += 1
            phoneme_index = 0
            current_consonants = self.get_consonants(group_index)

        if group_index == len(self.nonfinals) and phoneme_index >= len(current_consonants):
            return None

        return group_index, phoneme_index
    
    def get_consonant_after(self, group_index: int, phoneme_index: int):
        next_index = self.increment_consonant_index(group_index, phoneme_index)
        if next_index is None:
            return None
        
        return self.get_consonant(*next_index)
    
    def get_consonant_before(self, group_index: int, phoneme_index: int):
        last_index = self.decrement_consonant_index(group_index, phoneme_index)
        if last_index is None:
            return None
        
        return self.get_consonant(*last_index)

    def n_consonants_in_group(self, group_index: int):
        return len(self.get_consonants(group_index))

    def get_vowel_of_group(self, group_index: int):
        return self.nonfinals[group_index].vowel

    def is_last_group(self, group_index: int):
        return group_index == len(self.nonfinals)
    
    def next_sound(self, group_index: int, sound_index: int):
        next_index = self.increment_index(group_index, sound_index)
        if next_index is None:
            return None

        return self[next_index]

    def is_vowel(self, group_index: int, sound_index: int):
        if self.is_last_group(group_index):
            return False

        return sound_index == len(self.nonfinals[group_index].consonants)