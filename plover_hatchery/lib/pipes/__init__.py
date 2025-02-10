"""
Two types of elision:
    - squish (placing vowel between two consonant chords on the same side)
    - boundary (placing vowel on the transition from right to left consonant chords)
"""

from .consonants_vowels_enumeration import consonants_vowels_enumeration, ConsonantsVowelsEnumerationHooks
from .declare_banks import declare_banks
from .banks import banks, BanksApi, BanksState
from .initial_vowel_chord import initial_vowel_chord
from .left_squish_elision import left_squish_elision
from .right_squish_elision import right_squish_elision
from .boundary_elision import boundary_elision
from .left_alt_chords import left_alt_chords, LeftAltChordsHooks, LeftAltChordsState
from .left_alt_squish_elision import left_alt_squish_elision
from .right_alt_chords import right_alt_chords
from .right_alt_squish_elision import right_alt_squish_elision
from .clusters import consonant_clusters, vowel_clusters
from .linker_chord import linker_chord
from .splitter_lookup import splitter_lookup
from .path_traversal_reverse_lookup import path_traversal_reverse_lookup

from .Theory import Theory
from .compile_theory import compile_theory

from .define_sophones import define_sophones
from .sophone_mapper import sophone_to_strokes_mapper, sophone_to_sopheme_mapper
from .yield_if import yield_if, yield_stroke_if
from .map_unstressed_vowels import map_unstressed_vowels