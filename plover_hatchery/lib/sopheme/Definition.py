from dataclasses import dataclass
from typing import final

from plover_hatchery.lib.sopheme.Sopheme import Sopheme

@final
class Definition:
    def __init__(self, sophemes: tuple[Sopheme, ...]):
        self.sophemes = sophemes

        vowels: list[DefinitionCursor] = []
        for phoneme in self.phonemes():
            if phoneme.keysymbol.is_vowel:
                vowels.append(phoneme)
        
        self.vowels = tuple(vowels)


    def first_phoneme(self):
        new_sopheme_index = 0

        while new_sopheme_index < len(self.sophemes):
            if len(self.sophemes[new_sopheme_index].keysymbols) > 0:
                return DefinitionCursor(self, new_sopheme_index, 0)

            new_sopheme_index += 1

        return None

    def first_consonant(self):
        phoneme = self.first_phoneme()

        while phoneme is not None and not phoneme.keysymbol.is_consonant:
            phoneme = phoneme.next()
        
        return phoneme


    def last_phoneme(self):
        new_sopheme_index = len(self.sophemes) - 1

        while new_sopheme_index >= 0:
            if len(self.sophemes[new_sopheme_index].keysymbols) > 0:
                return DefinitionCursor(self, new_sopheme_index, len(self.sophemes[new_sopheme_index].keysymbols) - 1)

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
                yield DefinitionCursor(self, sopheme_index, keysymbol_index)

        for sopheme_index, sopheme in enumerate(self.sophemes):
            yield sopheme, yield_phonemes(sopheme_index, sopheme)


    def __str__(self):
        return " ".join(str(sopheme) for sopheme in self.sophemes)
    
    def __repr__(self):
        return f"SophemeSeq({str(self)})"



@final
@dataclass(frozen=True)
class DefinitionCursor:
    definition: Definition
    sopheme_index: int
    keysymbol_index: int

    @property
    def sopheme(self):
        return self.definition.sophemes[self.sopheme_index]

    @property
    def keysymbol(self):
        return self.sopheme.keysymbols[self.keysymbol_index]

    @property
    def indices(self):
        return (self.sopheme_index, self.keysymbol_index)


    def appears_before(self, phoneme: "DefinitionCursor"):
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

            new_keysymbol_index = len(self.definition.sophemes[new_sopheme_index].keysymbols) - 1

        return DefinitionCursor(self.definition, new_sopheme_index, new_keysymbol_index)


    def next(self):
        new_sopheme_index = self.sopheme_index
        new_keysymbol_index = self.keysymbol_index + 1

        while new_keysymbol_index >= len(self.definition.sophemes[new_sopheme_index].keysymbols):
            new_sopheme_index += 1
            if new_sopheme_index >= len(self.definition.sophemes):
                return None

            new_keysymbol_index = 0

        return DefinitionCursor(self.definition, new_sopheme_index, new_keysymbol_index)


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
        if len(self.definition.vowels) == 0:
            return True

        return self.appears_before(self.definition.vowels[0])

    def appears_after_last_vowel(self):
        if len(self.definition.vowels) == 0:
            return True
        
        return self.definition.vowels[-1].appears_before(self)

    
    def is_first_phoneme(self):
        return self == self.definition.first_phoneme()

    def is_last_phoneme(self):
        return self == self.definition.last_phoneme()

    
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