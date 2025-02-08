from typing import cast, TypeVar, Generic, Any, Protocol
from dataclasses import dataclass

from ..trie import  NondeterministicTrie
from ..sopheme import Sound
from .state import OutlineSounds
from .Hook import Hook, HookAttr
from .Plugin import Plugin


T = TypeVar("T")

class OnBegin(Protocol[T]):
    def __call__(self, *, trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str) -> T: ...
class OnConsonant(Protocol[T]):
    def __call__(self, *, state: T, consonant: Sound, group_index: int, sound_index: int) -> None: ...
class OnVowel(Protocol[T]):
    def __call__(self, *, state: T, vowel: Sound, group_index: int, sound_index: int) -> None: ...
class OnComplete(Protocol[T]):
    def __call__(self, *, state: T) -> None: ...

class ConsonantsVowelsEnumerationHooks(Generic[T]):
    on_begin = HookAttr(OnBegin[T])
    on_consonant = HookAttr(OnConsonant[T])
    on_vowel = HookAttr(OnVowel[T])
    on_complete = HookAttr(OnComplete[T])


def consonants_vowels_enumeration(
    *plugins: Plugin,
):
    hooks = ConsonantsVowelsEnumerationHooks()

    plugins_map: dict[int, Any] = {
        id(consonants_vowels_enumeration): hooks
    }
    def get_plugin(plugin: Plugin[T]):
        return cast(T, plugins_map.get(plugin.id))

    for plugin in plugins:
        if plugin.initialize is None: continue

        if plugin.id in plugins_map: raise ValueError("duplicate plugin")

        plugins_map[plugin.id] = plugin.initialize(get_plugin=get_plugin, base_hooks=hooks)


    def on_begin(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        states: dict[int, Any] = {}
        for handler in hooks.on_begin.handlers():
            states[plugin.id] = handler(trie=trie, sounds=sounds, translation=translation)
        return states

    def on_consonant(states: dict[int, Any], consonant: Sound, group_index: int, sound_index: int):
        for handler in hooks.on_consonant.handlers():
            handler(state=states.get(plugin.id), consonant=consonant, group_index=group_index, sound_index=sound_index)

    def on_vowel(states: dict[int, Any], vowel: Sound, group_index: int, sound_index: int):
        for handler in hooks.on_vowel.handlers():
            handler(state=states.get(plugin.id), vowel=vowel, group_index=group_index, sound_index=sound_index)

    def on_complete(states: dict[int, Any]):
        for handler in hooks.on_complete.handlers():
            handler(state=states.get(plugin.id))


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


