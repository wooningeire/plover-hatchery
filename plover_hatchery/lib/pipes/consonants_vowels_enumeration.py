from typing import cast, TypeVar, Generic, Any, Protocol, Callable, final
from enum import Enum
from collections.abc import Iterable

from plover_hatchery.lib.pipes.compile_theory import TheoryHooks
from plover_hatchery.lib.sopheme import SophemeSeq, SophemeSeqPhoneme

from ..trie import  NondeterministicTrie
from ..sopheme import Sopheme
from .Hook import Hook
from .Plugin import Plugin, define_plugin
from ..pipes.Theory import Theory


T = TypeVar("T")

@final
class ConsonantsVowelsEnumerationHooks:
    class ProcessSophemeSeq(Protocol):
        def __call__(self, *, sopheme_seq: SophemeSeq) -> Iterable[Sopheme]: ...
    class OnBegin(Protocol):
        def __call__(self, *, trie: NondeterministicTrie[str, int], sophemes: SophemeSeq, entry_id: int) -> Any: ...
    class OnConsonant(Protocol):
        def __call__(self, *, state: Any, phoneme: SophemeSeqPhoneme) -> None: ...
    class OnVowel(Protocol):
        def __call__(self, *, state: Any, phoneme: SophemeSeqPhoneme) -> None: ...
    class OnComplete(Protocol):
        def __call__(self, *, state: Any) -> None: ...


    process_sopheme_seq = Hook(ProcessSophemeSeq)
    begin = Hook(OnBegin)
    consonant = Hook(OnConsonant)
    vowel = Hook(OnVowel)
    complete = Hook(OnComplete)


def consonants_vowels_enumeration() -> Plugin[ConsonantsVowelsEnumerationHooks]:
    @define_plugin(consonants_vowels_enumeration)
    def plugin(base_hooks: TheoryHooks, **_):
        hooks = ConsonantsVowelsEnumerationHooks()


        def process_sopheme_seq(sopheme_seq: SophemeSeq):
            for plugin_id, handler in hooks.process_sopheme_seq.ids_handlers():
                sopheme_seq = SophemeSeq(tuple(handler(sopheme_seq=sopheme_seq)))
            return sopheme_seq


        def on_begin(trie: NondeterministicTrie[str, int], sophemes: SophemeSeq, entry_id: int):
            states: dict[int, Any] = {}
            for plugin_id, handler in hooks.begin.ids_handlers():
                states[plugin_id] = handler(trie=trie, sophemes=sophemes, entry_id=entry_id)
            return states

        def on_consonant(states: dict[int, Any], consonant: SophemeSeqPhoneme):
            for plugin_id, handler in hooks.consonant.ids_handlers():
                handler(state=states.get(plugin_id), phoneme=consonant)

        def on_vowel(states: dict[int, Any], vowel: SophemeSeqPhoneme):
            for plugin_id, handler in hooks.vowel.ids_handlers():
                handler(state=states.get(plugin_id), phoneme=vowel)

        def on_complete(states: dict[int, Any]):
            for plugin_id, handler in hooks.complete.ids_handlers():
                handler(state=states.get(plugin_id))


        @base_hooks.add_entry.listen(consonants_vowels_enumeration)
        def _(trie: NondeterministicTrie[str, int], sophemes: SophemeSeq, entry_id: int):
            sophemes = process_sopheme_seq(sophemes)

            states = on_begin(trie, sophemes, entry_id)

            for phoneme in sophemes.phonemes():
                if phoneme.keysymbol.is_vowel:
                    on_vowel(states, phoneme)
                else:
                    on_consonant(states, phoneme)

            on_complete(states)

        
        return hooks

    return plugin


