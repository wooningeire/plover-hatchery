from typing import Callable, TypeVar, Generic, Any, Protocol
from dataclasses import dataclass

from ..trie import  NondeterministicTrie
from ..sopheme import Sound
from .state import  OutlineSounds


T = TypeVar("T")
U = TypeVar("U")

@dataclass
class ConsonantsVowelsEnumerationPlugin(Generic[T]):
    class OnBegin(Protocol[U]):
        def __call__(self, *, trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str) -> U: ...
    class OnConsonant(Protocol[U]):
        def __call__(self, *, state: U, consonant: Sound, group_index: int, sound_index: int) -> None: ...
    class OnVowel(Protocol[U]):
        def __call__(self, *, state: U, vowel: Sound, group_index: int, sound_index: int) -> None: ...
    class OnComplete(Protocol[U]):
        def __call__(self, *, state: U) -> None: ...

    on_begin: OnBegin[T]
    on_consonant: OnConsonant[T]
    on_vowel: OnVowel[T]
    on_complete: OnComplete[T]


def consonants_vowels_enumeration(
    *plugins: ConsonantsVowelsEnumerationPlugin,
):
    def on_begin(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        return tuple(plugin.on_begin(trie=trie, sounds=sounds, translation=translation) for plugin in plugins)

    def on_consonant(states: tuple[Any, ...], consonant: Sound, group_index: int, sound_index: int):
        for plugin, state in zip(plugins, states):
            plugin.on_consonant(state=state, consonant=consonant, group_index=group_index, sound_index=sound_index)

    def on_vowel(states: tuple[Any, ...], vowel: Sound, group_index: int, sound_index: int):
        for plugin, state in zip(plugins, states):
            plugin.on_vowel(state=state, vowel=vowel, group_index=group_index, sound_index=sound_index)

    def on_complete(states: tuple[Any, ...]):
        for plugin, state in zip(plugins, states):
            plugin.on_complete(state=state)


    def add_entry(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        states = on_begin(trie, sounds, translation)

        for group_index, group in enumerate(sounds.nonfinals):
            for sound_index, consonant in enumerate(group.consonants):
                on_consonant(states, consonant, group_index, sound_index)

            on_vowel(states, group.vowel, group_index, len(group.consonants))

        for sound_index, consonant in enumerate(sounds.final_consonants):
            on_consonant(states, consonant, group_index, sound_index)

        on_complete(states)

    return add_entry


