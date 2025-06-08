from plover_hatchery_lib_rs import DefViewCursor
from plover_hatchery.lib.pipes.optionalizer import BaseOptionalizePredicate, create_optionalizer_with_user_condition
from plover_hatchery.lib.sopheme import DefinitionCursor


def _should_optionalize(optionalize_if: BaseOptionalizePredicate, cursor: DefViewCursor):
    keysymbol = cursor.tip().keysymbol()


    if not keysymbol.is_consonant:
        return False

    # Filter out starting and ending consonants
    if (
        tuple(cursor.index_stack) < tuple(cursor.view.first_consonant_loc)
        or tuple(cursor.view.last_consonant_loc) < tuple(cursor.index_stack)
    ):
        return False

    # Filter out consonants that are surrounded by stressed vowels
    # Filter out consonants that are not alone
    prev_keysymbol = cursor.prev_keysymbol_loc()
    if prev_keysymbol is not None:
        keysymbol = prev_keysymbol.tip().keysymbol()
        if keysymbol.is_consonant or keysymbol.stress != 0:
            return False

    next_keysymbol = cursor.next_keysymbol_loc()
    if next_keysymbol is not None:
        keysymbol = next_keysymbol.tip().keysymbol()
        if keysymbol.is_consonant or keysymbol.stress != 0:
            return False
        
    # Custom condition
    if not optionalize_if(cursor):
        return False

    return True


optional_unstressed_middle_consonants = create_optionalizer_with_user_condition(should_optionalize=_should_optionalize)
