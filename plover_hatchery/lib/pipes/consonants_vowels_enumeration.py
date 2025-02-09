from typing import cast, TypeVar, Generic, Any, Protocol, Callable, final

from plover_hatchery.lib.pipes.compile_theory import TheoryHooks

from ..trie import  NondeterministicTrie
from ..sopheme import Sound
from .state import OutlineSounds
from .Hook import Hook
from .Plugin import Plugin, define_plugin
from ..pipes.Theory import Theory


T = TypeVar("T")

@final
class ConsonantsVowelsEnumerationHooks:
    class OnBegin(Protocol):
        def __call__(self, *, trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str) -> Any: ...
    class OnConsonant(Protocol):
        def __call__(self, *, state: Any, consonant: Sound, group_index: int, sound_index: int) -> None: ...
    class OnVowel(Protocol):
        def __call__(self, *, state: Any, vowel: Sound, group_index: int, sound_index: int) -> None: ...
    class OnComplete(Protocol):
        def __call__(self, *, state: Any) -> None: ...


    begin = Hook(OnBegin)
    consonant = Hook(OnConsonant)
    vowel = Hook(OnVowel)
    complete = Hook(OnComplete)


def consonants_vowels_enumeration() -> Plugin[ConsonantsVowelsEnumerationHooks]:
    @define_plugin(consonants_vowels_enumeration)
    def plugin(base_hooks: TheoryHooks, **_):
        hooks = ConsonantsVowelsEnumerationHooks()


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


        @base_hooks.add_entry.listen(consonants_vowels_enumeration)
        def _(trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
            states = on_begin(trie, sounds, translation)

            for group_index, group in enumerate(sounds.nonfinals):
                for sound_index, consonant in enumerate(group.consonants):
                    on_consonant(states, consonant, group_index, sound_index)

                on_vowel(states, group.vowel, group_index, len(group.consonants))

            group_index = len(sounds.nonfinals)
            for sound_index, consonant in enumerate(sounds.final_consonants):
                on_consonant(states, consonant, group_index, sound_index)

            on_complete(states)

        
        return hooks

    return plugin


