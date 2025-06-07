from plover_hatchery_lib_rs import DefViewCursor
from plover_hatchery.lib.pipes.optionalizer import BaseOptionalizePredicate, create_optionalizer
from plover_hatchery.lib.sopheme import DefinitionCursor



def _should_optionalize(cursor: DefViewCursor):
    print(cursor)
    if (tip := cursor.tip()) is None:
        return False
    print(tip)
    if (keysymbol := tip.maybe_keysymbol) is None:
        return False


    if not keysymbol.is_vowel:
        return False

    # Filter out starting and ending consonants
    print(cursor.index_stack, cursor.view.first_consonant_loc, cursor.view.last_consonant_loc)
    if (
        tuple(cursor.index_stack) < tuple(cursor.view.first_consonant_loc)
        or tuple(cursor.view.last_consonant_loc) < tuple(cursor.index_stack)
    ):
        return False

    return True


optional_middle_vowels = create_optionalizer(should_optionalize=_should_optionalize)
