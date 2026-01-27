from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import TextIO

from plover.steno import Stroke
import plover.log


from ..trie import NondeterministicTrie
from ..pipes import Theory



def build_lookup_json(mappings: dict[str, str]):
    trie: NondeterministicTrie[str] = NondeterministicTrie()

    # for outline_steno, translation in mappings.items():
    #     phonemes = get_outline_phonemes(Stroke.from_steno(steno) for steno in outline_steno.split("/"))
    #     if phonemes is None:
    #         continue
    #     add_entry(trie, phonemes, translation)

    # plover.log.debug(str(trie))
    return lambda x: None, lambda x: []
    # return create_lookup_for(trie), create_reverse_lookup_for(trie)
