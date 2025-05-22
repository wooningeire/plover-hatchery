from plover_hatchery.lib.pipes.optionalizer import BaseOptionalizePredicate, create_optionalizer_with_user_condition
from plover_hatchery.lib.sopheme import DefinitionCursor



def _should_optionalize(optionalize_if: BaseOptionalizePredicate, phoneme: DefinitionCursor):
    if not phoneme.keysymbol.is_consonant:
        return False

    # Filter out starting and ending consonants
    if phoneme.appears_before_first_vowel() or phoneme.appears_after_last_vowel():
        return False

    # Custom condition
    if not optionalize_if(phoneme):
        return False

    return True


optional_middle_consonants = create_optionalizer_with_user_condition(should_optionalize=_should_optionalize)