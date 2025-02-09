from collections.abc import Callable, Iterable
from typing import TextIO

from plover.steno import Stroke
import plover.log

from plover_hatchery.lib.pipes.state import OutlineSounds

from ..trie import NondeterministicTrie
from ..sopheme import Sopheme
from ..pipes import Theory



def build_lookup_json(mappings: dict[str, str]):
    trie: NondeterministicTrie[str, str] = NondeterministicTrie()

    # for outline_steno, translation in mappings.items():
    #     phonemes = get_outline_phonemes(Stroke.from_steno(steno) for steno in outline_steno.split("/"))
    #     if phonemes is None:
    #         continue
    #     add_entry(trie, phonemes, translation)

    # plover.log.debug(str(trie))
    return lambda x: None, lambda x: []
    # return create_lookup_for(trie), create_reverse_lookup_for(trie)


def get_lookup_builder_hatchery(theory: Theory):
    def build_lookup_hatchery(entries: Iterable[str]):
        trie: NondeterministicTrie[str, str] = NondeterministicTrie()

        n_entries = 0
        n_passed_parses = 0
        n_passed_additions = 0

        for i, line in enumerate(entries):
            if i % 1000 == 0:
                print(f"hatched {i}")

            try:
                sophemes = tuple(Sopheme.parse_seq(line.strip()))
                n_passed_parses += 1

                try:
                    theory.add_entry(trie, sophemes, Sopheme.get_translation(sophemes))
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

        def lookup(stroke_stenos: tuple[str, ...]):
            return theory.lookup(trie, stroke_stenos)

        def reverse_lookup(translation: str):
            return theory.reverse_lookup(trie, translation)

        return lookup, reverse_lookup
    
    return build_lookup_hatchery