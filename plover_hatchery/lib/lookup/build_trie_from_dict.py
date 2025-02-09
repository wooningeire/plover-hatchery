from typing import TextIO

from plover.steno import Stroke
import plover.log

from ..trie import NondeterministicTrie
from ..sopheme import Sopheme
from ..theory_defaults.amphitheory_2 import add_entry
from .build_lookup import create_lookup_for
from .build_reverse_lookup import create_reverse_lookup_for
from .get_sophemes import get_sopheme_sounds



def build_lookup_json(mappings: dict[str, str]):
    trie: NondeterministicTrie[str, str] = NondeterministicTrie()

    # for outline_steno, translation in mappings.items():
    #     phonemes = get_outline_phonemes(Stroke.from_steno(steno) for steno in outline_steno.split("/"))
    #     if phonemes is None:
    #         continue
    #     add_entry(trie, phonemes, translation)

    # plover.log.debug(str(trie))
    return create_lookup_for(trie), create_reverse_lookup_for(trie)


def build_lookup_hatchery(file: TextIO):
    trie: NondeterministicTrie[str, str] = NondeterministicTrie()

    n_entries = 0
    n_passed_parses = 0
    n_passed_additions = 0

    for i, line in enumerate(file):
        if i % 1000 == 0:
            print(f"hatched {i}")

        try:
            sophemes = tuple(Sopheme.parse_seq(line.strip()))
            n_passed_parses += 1

            try:
                add_entry(trie, get_sopheme_sounds(sophemes), Sopheme.get_translation(sophemes))
                n_passed_additions += 1
            except Exception as e:
                # import traceback
                # print(f"failed to add {line.strip()}: {e} ({''.join(traceback.format_tb(e.__traceback__))})")
                pass
        except Exception as e:
            # print(f"failed to parse {line.strip()}: {e}")
            pass

        n_entries += 1
    # while len(line := file.readline()) > 0:
    #     _add_entry(trie, Sopheme.parse_seq())

    n_failed_additions = n_entries - n_passed_additions
    n_failed_parses = n_entries - n_passed_parses

    print(f"""
Hatched {n_entries} entries
    {n_failed_additions} ({n_failed_additions / n_entries:.3f}%) total failed additions
    ({n_failed_parses} ({n_failed_parses / n_entries:.3f}%) failed parsing)
""")

    return create_lookup_for(trie), create_reverse_lookup_for(trie)