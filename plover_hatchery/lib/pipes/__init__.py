"""
Two types of elision:
    - squish (placing vowel between two consonant chords on the same side)
    - boundary (placing vowel on the transition from right to left consonant chords)
"""

from .consonants_vowels_enumeration import consonants_vowels_enumeration, ConsonantsVowelsEnumerationHooks
from .declare_banks import declare_banks, BankStrokes
from .banks import banks, BanksApi, BanksState
from .initial_vowel_chord import initial_vowel_chord
from .diphthong_transition_consonants import diphthong_transition_consonants
from .optional_middle_vowels import optional_middle_vowels
from .optional_middle_consonants import optional_middle_consonants
from .optional_unstressed_middle_consonants import optional_unstressed_middle_consonants
from .alternate_chords import alternate_chords
from .clusters import consonant_clusters, vowel_clusters
from .linker_chord import linker_chord
from .key_by_key_lookup import key_by_key_lookup
from .path_traversal_reverse_lookup import path_traversal_reverse_lookup
from .lookup_result_filtering import lookup_result_filtering

from .Theory import Theory
from .compile_theory import compile_theory

from .SophoneType import SophoneType, Sophone
from .iter_helpers import *
from .phoneme_conditions import *