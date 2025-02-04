from ..trie import  NondeterministicTrie
from .state import  OutlineSounds, ConsonantVowelGroup
from .Hook import Hook

class SoundsEnumerator:
    def __init__(self):
        self.begin: Hook[NondeterministicTrie[str, str], OutlineSounds, str] = Hook()
        self.begin_group: Hook[int] = Hook()
        self.consonant: Hook[int] = Hook()
        self.vowel: Hook[ConsonantVowelGroup] = Hook()
        self.complete: Hook[()] = Hook()

    def execute(self, trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        self.begin.emit(trie, sounds, translation)

        for group_index, group in enumerate(sounds.nonfinals):
            self.begin_group.emit(group_index)

            for phoneme_index, consonant in enumerate(group.consonants):
                self.consonant.emit(phoneme_index)

            self.vowel.emit(group)

        self.begin_group.emit(len(sounds.nonfinals))

        for phoneme_index, consonant in enumerate(sounds.final_consonants):
            self.consonant.emit(phoneme_index)

        self.complete.emit()