from plover_hatchery.lib.pipes.optionalizer import BaseOptionalizePredicate, create_optionalizer
from plover_hatchery.lib.sopheme import SophemeSeqPhoneme



def _should_optionalize(phoneme: SophemeSeqPhoneme):
    if not phoneme.keysymbol.is_vowel:
        return False

    # Filter out starting and ending consonants
    if phoneme.is_first_phoneme() or phoneme.is_last_phoneme():
        return False

    return True


optional_middle_vowels = create_optionalizer(should_optionalize=_should_optionalize)
