from typing import cast, TypeVar, Generic, Any, Protocol, Callable, final
from enum import Enum
from collections.abc import Iterable

from plover_hatchery.lib.pipes.compile_theory import TheoryHooks

from ..trie import  NondeterministicTrie
from ..sopheme import Sound, Sopheme
from .state import OutlineSounds, ConsonantVowelGroup
from .Hook import Hook
from .Plugin import Plugin, define_plugin
from ..pipes.Theory import Theory


T = TypeVar("T")

@final
class ConsonantsVowelsEnumerationHooks:
    class OnBegin(Protocol):
        def __call__(self, *, trie: NondeterministicTrie[str, int], sounds: OutlineSounds, entry_id: int) -> Any: ...
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


def consonants_vowels_enumeration(vowel_diphthong_transition: Callable[[Sound], "Sopheme | None"]) -> Plugin[ConsonantsVowelsEnumerationHooks]:
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
            diphthong_transition_sopheme = vowel_diphthong_transition(prev_vowel)
            if diphthong_transition_sopheme is None: return

            self.__current_group_consonants.append(Sound(diphthong_transition_sopheme.keysymbols[0], diphthong_transition_sopheme))


        def add_consonant(self, consonant: Sound):
            self.__current_group_consonants.append(consonant)
        

        def add_vowel(self, vowel: Sound):
            # self.__append_diphthong_transition()

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


    @define_plugin(consonants_vowels_enumeration)
    def plugin(base_hooks: TheoryHooks, **_):
        hooks = ConsonantsVowelsEnumerationHooks()


        def on_begin(trie: NondeterministicTrie[str, int], sounds: OutlineSounds, entry_id: int):
            states: dict[int, Any] = {}
            for plugin_id, handler in hooks.begin.ids_handlers():
                states[plugin_id] = handler(trie=trie, sounds=sounds, entry_id=entry_id)
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
        def _(trie: NondeterministicTrie[str, int], sophemes: Iterable[Sopheme], entry_id: int):
            sounds = get_sopheme_sounds(sophemes)

            states = on_begin(trie, sounds, entry_id)

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


