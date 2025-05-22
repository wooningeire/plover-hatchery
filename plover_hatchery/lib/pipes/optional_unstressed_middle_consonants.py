from plover_hatchery.lib.pipes.optionalizer import BaseOptionalizePredicate, create_optionalizer_with_user_condition
from plover_hatchery.lib.sopheme import DefinitionCursor


def _should_optionalize(optionalize_if: BaseOptionalizePredicate, phoneme: DefinitionCursor):
    if not phoneme.keysymbol.is_consonant:
        return False

    # Filter out starting and ending consonants
    if phoneme.appears_before_first_vowel() or phoneme.appears_after_last_vowel():
        return False

    # Filter out consonants that are surrounded by stressed vowels
    prev_vowel = phoneme.prev_vowel()
    if prev_vowel is not None and prev_vowel.keysymbol.stress != 0:
        return False

    next_vowel = phoneme.next_vowel()
    if next_vowel is not None and next_vowel.keysymbol.stress != 0:
        return False
        
    # Filter out consonants that are not alone
    if not phoneme.is_lone_consonant():
        return False

    # Custom condition
    if not optionalize_if(phoneme):
        return False

    return True


optional_unstressed_middle_consonants = create_optionalizer_with_user_condition(should_optionalize=_should_optionalize)
