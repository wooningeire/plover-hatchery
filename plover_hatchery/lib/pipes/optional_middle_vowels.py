from plover_hatchery_lib_rs import DefViewCursor
from plover_hatchery.lib.pipes.optionalizer import BaseOptionalizePredicate, create_optionalizer
from plover_hatchery.lib.sopheme import DefinitionCursor



def _should_optionalize(cursor: DefViewCursor):
    keysymbol = cursor.tip().keysymbol()

    if not keysymbol.is_vowel:
        return False

    # Filter out starting and ending consonants
    if (
        tuple(cursor.index_stack) < tuple(cursor.view.first_consonant_loc)
        or tuple(cursor.view.last_consonant_loc) < tuple(cursor.index_stack)
    ):
        return False

    return True


optional_middle_vowels = create_optionalizer(should_optionalize=_should_optionalize)
