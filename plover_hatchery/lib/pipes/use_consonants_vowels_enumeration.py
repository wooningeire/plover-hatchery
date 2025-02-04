from typing import Callable, TypeVar

from ..trie import  NondeterministicTrie
from ..sopheme import Sound
from .state import  OutlineSounds, ConsonantVowelGroup


T = TypeVar("T")

def use_consonants_vowels_enumeration(
    *,
    on_begin: Callable[[NondeterministicTrie[str, str], OutlineSounds, str], T],
    on_consonant: Callable[[T, Sound], None],
    on_vowel: Callable[[T, Sound], None],
    on_complete: Callable[[T], None],
):
    def add_entry(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        state = on_begin(trie, sounds, translation)

        for group_index, group in enumerate(sounds.nonfinals):
            for phoneme_index, consonant in enumerate(group.consonants):
                on_consonant(state, consonant)

            on_vowel(state, group.vowel)

        for phoneme_index, consonant in enumerate(sounds.final_consonants):
            on_consonant(state, consonant)

        on_complete(state)

    return add_entry