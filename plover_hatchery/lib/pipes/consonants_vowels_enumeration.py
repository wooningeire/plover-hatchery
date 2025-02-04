from typing import Callable, TypeVar, Generic, Any
from dataclasses import dataclass

from ..trie import  NondeterministicTrie
from ..sopheme import Sound
from .state import  OutlineSounds, ConsonantVowelGroup


T = TypeVar("T")

@dataclass
class ConsonantsVowelsEnumerationPlugin(Generic[T]):
    on_begin: Callable[[NondeterministicTrie[str, str], OutlineSounds, str], T]
    on_consonant: Callable[[T, Sound], None]
    on_vowel: Callable[[T, Sound], None]
    on_complete: Callable[[T], None]


def consonants_vowels_enumeration(
    *plugins: ConsonantsVowelsEnumerationPlugin,
):
    def on_begin(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        return tuple(plugin.on_begin(trie, sounds, translation) for plugin in plugins)

    def on_consonant(states: tuple[Any, ...], consonant: Sound):
        for plugin, state in zip(plugins, states):
            plugin.on_consonant(state, consonant)

    def on_vowel(states: tuple[Any, ...], vowel: Sound):
        for plugin, state in zip(plugins, states):
            plugin.on_vowel(state, vowel)

    def on_complete(states: tuple[Any, ...]):
        for plugin, state in zip(plugins, states):
            plugin.on_complete(state)


    def add_entry(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        states = on_begin(trie, sounds, translation)

        for group_index, group in enumerate(sounds.nonfinals):
            for phoneme_index, consonant in enumerate(group.consonants):
                on_consonant(states, consonant)

            on_vowel(states, group.vowel)

        for phoneme_index, consonant in enumerate(sounds.final_consonants):
            on_consonant(states, consonant)

        on_complete(states)

    return add_entry


