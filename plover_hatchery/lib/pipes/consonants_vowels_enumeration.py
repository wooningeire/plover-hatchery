from typing import cast, TypeVar, Generic, Any, Protocol, Callable
from dataclasses import dataclass

from ..trie import  NondeterministicTrie
from ..sopheme import Sound
from .state import OutlineSounds
from .Hook import Hook
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
    begin = Hook(OnBegin[T])
    consonant = Hook(OnConsonant[T])
    vowel = Hook(OnVowel[T])
    complete = Hook(OnComplete[T])


def consonants_vowels_enumeration(
    *plugins: Plugin[Any],
):
    hooks = ConsonantsVowelsEnumerationHooks()

    plugins_map: dict[int, Any] = {}
    def get_plugin_api(plugin_factory: Callable[..., Plugin[T]]) -> T:
        plugin_id = id(plugin_factory)

        if plugin_id not in plugins_map:
            raise ValueError("plugin not found")
        
        return cast(T, plugins_map[plugin_id])


    for plugin in plugins:
        if plugin.id in plugins_map: raise ValueError("duplicate plugin")

        plugins_map[plugin.id] = plugin.initialize(get_plugin_api=get_plugin_api, base_hooks=hooks)


    def on_begin(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        states: dict[int, Any] = {}
        for plugin_id, handler in hooks.begin.ids_handlers():
            states[plugin_id] = handler(trie=trie, sounds=sounds, translation=translation)
        return states

    def on_consonant(states: dict[int, Any], consonant: Sound, group_index: int, sound_index: int):
        for plugin_id, handler in hooks.consonant.ids_handlers():
            handler(state=states.get(plugin_id), consonant=consonant, group_index=group_index, sound_index=sound_index)

    def on_vowel(states: dict[int, Any], vowel: Sound, group_index: int, sound_index: int):
        for plugin_id, handler in hooks.vowel.ids_handlers():
            handler(state=states.get(plugin_id), vowel=vowel, group_index=group_index, sound_index=sound_index)

    def on_complete(states: dict[int, Any]):
        for plugin_id, handler in hooks.complete.ids_handlers():
            handler(state=states.get(plugin_id))


    def add_entry(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        states = on_begin(trie, sounds, translation)

        for group_index, group in enumerate(sounds.nonfinals):
            for sound_index, consonant in enumerate(group.consonants):
                on_consonant(states, consonant, group_index, sound_index)

            on_vowel(states, group.vowel, group_index, len(group.consonants))

        group_index = len(sounds.nonfinals)
        for sound_index, consonant in enumerate(sounds.final_consonants):
            on_consonant(states, consonant, group_index, sound_index)

        on_complete(states)

    return add_entry


