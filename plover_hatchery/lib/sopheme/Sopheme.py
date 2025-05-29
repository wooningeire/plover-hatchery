from collections.abc import Iterable
from plover_hatchery_lib_rs import Sopheme

def get_sopheme_seq_translation(sophemes: "Iterable[Sopheme]"):
    return "".join(sopheme.chars for sopheme in sophemes)