

/*
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
*/