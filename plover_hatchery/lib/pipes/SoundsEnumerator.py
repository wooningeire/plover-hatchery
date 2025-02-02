from ..trie import  NondeterministicTrie
from .state import  OutlineSounds, ConsonantVowelGroup
from .Hook import Hook

class SoundsEnumerator:
    def __init__(self):
        self.begin: Hook[NondeterministicTrie[str, str], OutlineSounds, str] = Hook()
        self.begin_nonfinal_group: Hook[int, ConsonantVowelGroup] = Hook()
        self.nonfinal_consonant: Hook[int] = Hook()
        self.complete_nonfinal_group: Hook[ConsonantVowelGroup] = Hook()
        self.begin_final_group: Hook[int] = Hook()
        self.final_consonant: Hook[int] = Hook()
        self.complete: Hook[()] = Hook()

    def execute(self, trie: NondeterministicTrie[str, str], sounds: OutlineSounds, translation: str):
        self.begin.emit(trie, sounds, translation)

        for group_index, group in enumerate(sounds.nonfinals):
            self.begin_nonfinal_group.emit(group_index, group)

            for phoneme_index, consonant in enumerate(group.consonants):
                self.nonfinal_consonant.emit(phoneme_index)

            self.complete_nonfinal_group.emit(group)

        self.begin_final_group.emit(len(sounds.nonfinals))

        for phoneme_index, consonant in enumerate(sounds.final_consonants):
            self.final_consonant.emit(phoneme_index)

        self.complete.emit()