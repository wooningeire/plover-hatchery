from plover_hatchery_lib_rs import DefViewCursor
from plover_hatchery.lib.pipes.optionalizer import BaseOptionalizePredicate, create_optionalizer_with_user_condition
from plover_hatchery.lib.sopheme import DefinitionCursor



def _should_optionalize(optionalize_if: BaseOptionalizePredicate, cursor: DefViewCursor):
    if (tip := cursor.maybe_tip()) is None:
        return False
    if (keysymbol := tip.maybe_keysymbol) is None:
        return False

    if not keysymbol.is_consonant:
        return False

    # Filter out starting and ending consonants
    if (
        tuple(cursor.index_stack) < tuple(cursor.view.first_vowel_loc)
        or tuple(cursor.view.last_vowel_loc) < tuple(cursor.index_stack)
    ):
        return False

    # Custom condition
    if not optionalize_if(cursor):
        return False

    return True


optional_middle_consonants = create_optionalizer_with_user_condition(should_optionalize=_should_optionalize)