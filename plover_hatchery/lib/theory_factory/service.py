
from plover.steno import Stroke

from ..sophone.Sophone import Sophone
from ..sopheme import Keysymbol, Sound
from .spec import TheorySpec
from ..trie import Trie, ReadonlyTrie

class TheoryService:
    def __init__(self, spec: type[TheorySpec]):
        self.spec = spec

        self.clusters_trie = self.__build_clusters_trie()
        self.vowel_clusters_trie = self.__build_vowel_clusters_trie()
        self.__split_consonant_phonemes = self.__build_consonants_splitter()
        self.chords_to_phonemes_vowels = self.__build_chords_to_phonemes_vowels()

    @staticmethod
    def theory(spec: type[TheorySpec]) -> "TheoryService":
        assert not (spec.LINKER_CHORD & ~spec.LEFT_BANK_CONSONANTS_SUBSTROKE), "Linker chord must only consist of starter keys"

        return TheoryService(spec)

    def __build_clusters_trie(self) -> ReadonlyTrie[Sophone, Stroke]:
        clusters_trie: Trie[Sophone, Stroke] = Trie()
        for phonemes, stroke in self.spec.CLUSTERS.items():
            current_head = clusters_trie.ROOT
            for key in phonemes:
                current_head = clusters_trie.get_dst_node_else_create(current_head, key)

            clusters_trie.set_translation(current_head, stroke)
        return clusters_trie.frozen()
    
    def __build_vowel_clusters_trie(self) -> ReadonlyTrie["Sophone | Stroke", Stroke]:
        clusters_trie: "Trie[Sophone | Stroke, Stroke]" = Trie()
        for phonemes, stroke in self.spec.VOWEL_CONSCIOUS_CLUSTERS.items():
            current_head = clusters_trie.ROOT
            for key in phonemes:
                current_head = clusters_trie.get_dst_node_else_create(current_head, key)

            clusters_trie.set_translation(current_head, stroke)
        return clusters_trie.frozen()
    
    def __build_consonants_splitter(self):
        _CONSONANT_CHORDS: dict[Stroke, tuple[Sophone, ...]] = {
            **{
                stroke: (phoneme,)
                for phoneme, stroke in self.spec.PHONEMES_TO_CHORDS_LEFT.items()
            },
            **{
                stroke: (phoneme,)
                for phoneme, stroke in self.spec.PHONEMES_TO_CHORDS_RIGHT.items()
            },

            **{
                Stroke.from_steno(steno): phonemes
                for steno, phonemes in {
                    "PHR": (Sophone.P, Sophone.L),
                    "TPHR": (Sophone.F, Sophone.L),
                }.items()
            },
        }

        def _build_consonants_trie():
            consonants_trie: Trie[str, tuple[Sophone, ...]] = Trie()
            for stroke, _phoneme in _CONSONANT_CHORDS.items():
                current_head = consonants_trie.get_dst_node_else_create_chain(consonants_trie.ROOT, stroke.keys())
                consonants_trie.set_translation(current_head, _phoneme)
            return consonants_trie.frozen()
        _consonants_trie = _build_consonants_trie()


        def split_consonant_phonemes(consonants_stroke: Stroke):
            keys = consonants_stroke.keys()
            
            chord_start_index = 0
            while chord_start_index < len(keys):
                current_node = _consonants_trie.ROOT

                longest_chord_end_index = chord_start_index

                entry: tuple[Sophone, ...] = ()

                for seek_index in range(chord_start_index, len(keys)):
                    key = keys[seek_index]
                    
                    current_node = _consonants_trie.get_dst_node(current_node, key)
                    if current_node is None:
                        break

                    new_entry = _consonants_trie.get_translation(current_node)
                    if new_entry is None:
                        continue
                
                    entry = new_entry
                    longest_chord_end_index = seek_index

                yield from entry

                chord_start_index = longest_chord_end_index + 1
        
        return split_consonant_phonemes
    
    def __build_chords_to_phonemes_vowels(self):
        return {
            stroke: phoneme
            for phoneme, stroke in self.spec.PHONEMES_TO_CHORDS_VOWELS.items()
        }
    
    def sound_sophone(self, sound: Sound):
        spelled = {
            "a": Sophone.A,
            "e": Sophone.E,
            "i": Sophone.I,
            "o": Sophone.O,
            "u": Sophone.U,
        }.get(sound.sopheme.chars)

        return {
            "p": (Sophone.P,),
            "t": (Sophone.T, Sophone.D),
            "?": (),  # glottal stop
            "t^": (Sophone.T, Sophone.R),  # tapped R
            "k": (Sophone.K,),
            "x": (Sophone.K,),
            "b": (Sophone.B,),
            "d": (Sophone.D, Sophone.T),
            "g": (Sophone.G,),
            "ch": (Sophone.CH,),
            "jh": (Sophone.J,),
            "s": (Sophone.S,),
            "z": (Sophone.Z,),
            "sh": (Sophone.SH,),
            "zh": (Sophone.SH, Sophone.J),
            "f": (Sophone.F,),
            "v": (Sophone.V,),
            "th": (Sophone.TH,),
            "dh": (Sophone.TH,),
            "h": (Sophone.H,),
            "m": (Sophone.M,),
            "m!": (Sophone.M,),
            "n": (Sophone.N,),
            "n!": (Sophone.N,),
            "ng": (Sophone.NG,),
            "l": (Sophone.L,),
            "ll": (Sophone.L,),
            "lw": (Sophone.L,),
            "l!": (Sophone.L,),
            "r": (Sophone.R,),
            "y": (Sophone.Y,),
            "w": (Sophone.W,),
            "hw": (Sophone.W,),
            
            "e": (Sophone.E, Sophone.EE, Sophone.AA),
            "ao": (Sophone.A, Sophone.AA, Sophone.O, Sophone.U),
            "a": (Sophone.A, Sophone.AA),
            "ah": (Sophone.A, Sophone.O),
            "oa": (Sophone.A, Sophone.O, Sophone.U),
            "aa": (Sophone.O, Sophone.A),
            "ar": (Sophone.A,),
            "eh": (Sophone.A,),
            "ou": (Sophone.OO, Sophone.O),
            "ouw": (Sophone.OO,),
            "oou": (Sophone.OO,),
            "o": (Sophone.O,),
            "au": (Sophone.O, Sophone.A),
            "oo": (Sophone.O,),
            "or": (Sophone.O,),
            "our": (Sophone.O,),
            "ii": (Sophone.EE,),
            "iy": (Sophone.EE,),
            "i": (Sophone.I, Sophone.EE, Sophone.E),
            "@r": (spelled,),
            "@": (spelled,),
            "uh": (Sophone.U,),
            "u": (Sophone.U, Sophone.O, Sophone.OO),
            "uu": (Sophone.UU,),
            "iu": (Sophone.UU,),
            "ei": (Sophone.AA, Sophone.E),
            "ee": (Sophone.AA, Sophone.E, Sophone.A),
            "ai": (Sophone.II,),
            "ae": (Sophone.II,),
            "aer": (Sophone.II,),
            "aai": (Sophone.II,),
            "oi": (Sophone.OI,),
            "oir": (Sophone.OI,),
            "ow": (Sophone.OU,),
            "owr": (Sophone.OU,),
            "oow": (Sophone.OU,),
            "ir": (Sophone.EE,),
            "@@r": (spelled,),
            "er": (Sophone.E, Sophone.U),
            "eir": (Sophone.E,),
            "ur": (Sophone.U, Sophone.UU),
            "i@": (spelled,),
        }[sound.keysymbol.base_symbol][0]
    
    def left_consonant_strokes(self, sound: Sound):
        if sound.sopheme.chars == "c" and Sophone.S == self.sound_sophone(sound):
            yield Stroke.from_steno("KPW")

        # for sophone in self.sound_sophone(sound):
        #     for stroke in self.spec.PHONEMES_TO_CHORDS_LEFT[sophone]:
        #         yield stroke
        yield self.spec.PHONEMES_TO_CHORDS_LEFT[self.sound_sophone(sound)]
    
    def right_consonant_strokes(self, sound: Sound):
        # for sophone in self.sound_sophone(sound):
        #     for stroke in self.spec.PHONEMES_TO_CHORDS_RIGHT[sophone]:
        #         yield stroke
        yield self.spec.PHONEMES_TO_CHORDS_RIGHT[self.sound_sophone(sound)]
    
    def right_alt_consonant_strokes(self, sound: Sound):
        # for sophone in self.sound_sophone(sound):
        #     for stroke in self.spec.PHONEMES_TO_CHORDS_RIGHT_ALT[sophone]:
        #         yield stroke
        yield self.spec.PHONEMES_TO_CHORDS_RIGHT_ALT[self.sound_sophone(sound)]
    
    def split_consonant_phonemes(self, stroke: Stroke):
        return self.__split_consonant_phonemes(stroke)
    
    def can_add_stroke_on(self, src_stroke: Stroke, addon_stroke: Stroke):
        return (
            len(src_stroke - self.spec.ASTERISK_SUBSTROKE) == 0
            or len(addon_stroke - self.spec.ASTERISK_SUBSTROKE) == 0
            or Stroke.from_keys(((src_stroke - self.spec.ASTERISK_SUBSTROKE).keys()[-1],)) < Stroke.from_keys(((addon_stroke - self.spec.ASTERISK_SUBSTROKE).keys()[0],))
        )

    def split_stroke_parts(self, stroke: Stroke):
        left_bank_consonants = stroke & self.spec.LEFT_BANK_CONSONANTS_SUBSTROKE
        vowels = stroke & self.spec.VOWELS_SUBSTROKE
        right_bank_consonants = stroke & self.spec.RIGHT_BANK_CONSONANTS_SUBSTROKE
        asterisk = stroke & self.spec.ASTERISK_SUBSTROKE

        return left_bank_consonants, vowels, right_bank_consonants, asterisk