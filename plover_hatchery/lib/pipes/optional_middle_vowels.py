from plover_hatchery_lib_rs import DefViewCursor
from plover_hatchery.lib.pipes.optionalizer import create_optionalizer


def _should_optionalize(cursor: DefViewCursor):
    keysymbol = cursor.tip().keysymbol()

    if not keysymbol.is_vowel:
        return False

    # Filter out starting and ending consonants
    if cursor.occurs_after_last_consonant() or cursor.occurs_after_last_consonant():
        return False

    return True


optional_middle_vowels = create_optionalizer(should_optionalize=_should_optionalize)
