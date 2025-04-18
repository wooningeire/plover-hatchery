from dataclasses import dataclass
from typing import final

from plover_hatchery.lib.sopheme.Sopheme import Sopheme

@final
class SophemeSeq:
    def __init__(self, sophemes: tuple[Sopheme, ...]):
        self.sophemes = sophemes

        vowels: list[SophemeSeqPhoneme] = []
        for phoneme in self.phonemes():
            if phoneme.keysymbol.is_vowel:
                vowels.append(phoneme)
        
        self.vowels = tuple(vowels)


    def first_phoneme(self):
        new_sopheme_index = 0

        while new_sopheme_index < len(self.sophemes):
            if len(self.sophemes[new_sopheme_index].keysymbols) > 0:
                return SophemeSeqPhoneme(self, new_sopheme_index, 0)

            new_sopheme_index += 1

        return None


    def last_phoneme(self):
        new_sopheme_index = len(self.sophemes) - 1

        while new_sopheme_index >= 0:
            if len(self.sophemes[new_sopheme_index].keysymbols) > 0:
                return SophemeSeqPhoneme(self, new_sopheme_index, len(self.sophemes[new_sopheme_index].keysymbols) - 1)

            new_sopheme_index -= 1

        return None

    
    def phonemes(self):
        current_phoneme = self.first_phoneme()

        while current_phoneme is not None:
            yield current_phoneme
            current_phoneme = current_phoneme.next()

    
    def phonemes_by_sopheme(self):
        def yield_phonemes(sopheme_index: int, sopheme: Sopheme):
            for keysymbol_index, keysymbol in enumerate(sopheme.keysymbols):
                yield SophemeSeqPhoneme(self, sopheme_index, keysymbol_index)

        for sopheme_index, sopheme in enumerate(self.sophemes):
            yield sopheme, yield_phonemes(sopheme_index, sopheme)



@final
@dataclass(frozen=True)
class SophemeSeqPhoneme:
    seq: SophemeSeq
    sopheme_index: int
    keysymbol_index: int

    @property
    def sopheme(self):
        return self.seq.sophemes[self.sopheme_index]

    @property
    def keysymbol(self):
        return self.sopheme.keysymbols[self.keysymbol_index]

    @property
    def indices(self):
        return (self.sopheme_index, self.keysymbol_index)


    def appears_before(self, phoneme: "SophemeSeqPhoneme"):
        if self.sopheme_index < phoneme.sopheme_index:
            return True

        if self.keysymbol_index < phoneme.keysymbol_index:
            return True

        return False



    def prev(self):
        new_sopheme_index = self.sopheme_index
        new_keysymbol_index = self.keysymbol_index - 1

        while new_keysymbol_index < 0:
            new_sopheme_index -= 1
            if new_sopheme_index < 0:
                return None

            new_keysymbol_index = len(self.seq.sophemes[new_sopheme_index].keysymbols) - 1

        return SophemeSeqPhoneme(self.seq, new_sopheme_index, new_keysymbol_index)


    def next(self):
        new_sopheme_index = self.sopheme_index
        new_keysymbol_index = self.keysymbol_index + 1

        while new_keysymbol_index >= len(self.seq.sophemes[new_sopheme_index].keysymbols):
            new_sopheme_index += 1
            if new_sopheme_index >= len(self.seq.sophemes):
                return None

            new_keysymbol_index = 0

        return SophemeSeqPhoneme(self.seq, new_sopheme_index, new_keysymbol_index)


    def prev_consonant(self):
        current_phoneme = self.prev()

        while current_phoneme is not None and not current_phoneme.keysymbol.is_consonant:
            current_phoneme = current_phoneme.prev()

        return current_phoneme


    def next_consonant(self):
        current_phoneme = self.next()

        while current_phoneme is not None and not current_phoneme.keysymbol.is_consonant:
            current_phoneme = current_phoneme.next()

        return current_phoneme

    def prev_vowel(self):
        current_phoneme = self.prev()

        while current_phoneme is not None and not current_phoneme.keysymbol.is_vowel:
            current_phoneme = current_phoneme.prev()

        return current_phoneme


    def next_vowel(self):
        current_phoneme = self.next()

        while current_phoneme is not None and not current_phoneme.keysymbol.is_vowel:
            current_phoneme = current_phoneme.next()

        return current_phoneme

    
    def appears_before_first_vowel(self):
        if len(self.seq.vowels) == 0:
            return True

        return self.appears_before(self.seq.vowels[0])

    def appears_after_last_vowel(self):
        if len(self.seq.vowels) == 0:
            return True
        
        return self.seq.vowels[-1].appears_before(self)

    
    def is_first_phoneme(self):
        return self == self.seq.first_phoneme()

    def is_last_phoneme(self):
        return self == self.seq.last_phoneme()

    
    def is_lone_consonant(self):
        if not self.keysymbol.is_consonant:
            return False

        prev_phoneme = self.prev()
        if prev_phoneme is not None and prev_phoneme.keysymbol.is_consonant:
            return False

        next_phoneme = self.next()
        if next_phoneme is not None and next_phoneme.keysymbol.is_consonant:
            return False

        return True


    def __repr__(self):
        return f"SophemeSeqPhoneme[{self.sopheme} {self.keysymbol} ({self.sopheme_index} {self.keysymbol_index})]"