from plover_hatchery_lib_rs import DefViewCursor
from plover_hatchery.lib.pipes.optionalizer import BaseOptionalizePredicate, create_optionalizer_with_user_condition



def _should_optionalize(optionalize_if: BaseOptionalizePredicate, cursor: DefViewCursor):
    if (tip := cursor.maybe_tip()) is None:
        return False
    if (keysymbol := tip.maybe_keysymbol) is None:
        return False

    if not keysymbol.is_consonant:
        return False

    # Filter out starting and ending consonants
    if cursor.occurs_before_first_vowel() or cursor.occurs_after_last_vowel():
        return False

    # Custom condition
    if not optionalize_if(cursor):
        return False

    return True


optional_middle_consonants = create_optionalizer_with_user_condition(should_optionalize=_should_optionalize)