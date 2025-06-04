"""
Two types of elision:
    - squish (placing vowel between two consonant chords on the same side)
    - boundary (placing vowel on the transition from right to left consonant chords)
"""

from .soph_trie import soph_trie
from .diphthong_transition_consonants import diphthong_transition_consonants
from .optional_middle_vowels import optional_middle_vowels
from .optional_middle_consonants import optional_middle_consonants
from .optional_unstressed_middle_consonants import optional_unstressed_middle_consonants
from .alt_chords import alt_chords
# from .linker_chord import linker_chord
from .floating_keys import floating_keys
from .amphitheory_outlines import amphitheory_outlines
from .conflict_cycler_stroke import conflict_cycler_stroke
from .debug_stroke import debug_stroke
from .prohibited_strokes import prohibited_strokes
from .consonant_inversions import consonant_inversions

from .Theory import Theory
from .compile_theory import compile_theory

from .SophoneType import SophoneType, Sophone
from .iter_helpers import *
# from .phoneme_conditions import *
from .stroke_conditions import *
from .types import *