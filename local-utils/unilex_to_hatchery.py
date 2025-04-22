from collections import defaultdict
from typing import Any


from pathlib import Path
import json
import os
from dataclasses import dataclass
import timeit
import argparse
    
from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry

from plover_hatchery.lib.alignment.parse_morphology import AffixKey, Formatting, FreeMorpheme




def _setup_plover():
    registry.update()
    system.setup(DEFAULT_SYSTEM_NAME)



def _main(args: argparse.Namespace):
    from plover_hatchery.lib.sopheme import Sopheme
    from plover_hatchery.lib.alignment.match_sophemes import match_keysymbols_to_chars
    from plover_hatchery.lib.alignment.parse_morphology import split_morphology, Affix, MorphologyPart
    from plover_hatchery.lib.alignment.match_morphology import match_morphology_to_chars


    root = Path(os.getcwd())

    # with open(root / args.in_json_path, "r", encoding="utf-8") as file:
    #     lapwing_dict = json.load(file)
    
    # # reverse_lapwing_affixes_dict: dict[str, set[str]] = {}
    # reverse_lapwing_dict: dict[str, list[str]] = {}
    # for outline_steno, translation in lapwing_dict.items():
    #     # if "{^" in translation or "^}" in translation:
    #     #     if translation in reverse_lapwing_affixes_dict:
    #     #         reverse_lapwing_affixes_dict[_Affix(re.sub(translation, ))].add(outline_steno) 

    #     #     continue

    #     if not translation.isalnum():
    #         continue

    #     n_strokes = len(outline_steno.split("/"))
    #     if translation in reverse_lapwing_dict and n_strokes == len(reverse_lapwing_dict[translation][0].split("/")):
    #         reverse_lapwing_dict[translation].append(outline_steno)
    #         continue
    #     elif translation in reverse_lapwing_dict and n_strokes < len(reverse_lapwing_dict[translation][0].split("/")):
    #         continue

    #     reverse_lapwing_dict[translation] = [outline_steno]

    
    out_path = root / args.out_path
    out_path.parent.mkdir(exist_ok=True, parents=True)

    def generate():
        @dataclass(frozen=True)
        class Entry:
            translation: str
            morphology_parts: tuple[MorphologyPart, ...]

            def __str__(self):
                # return " ".join(str(sopheme) for sopheme in self.sophemes)

                entry_parts: list[str] = []
                for part in self.morphology_parts:
                    if isinstance(part, Formatting):
                        entry_parts.append(f"{part.ortho}.")
                        continue

                    if isinstance(part, Affix):
                        entry_parts.append("{" + affix_full_varname(part) + "}")
                        continue

                    phono = " ".join(bound.phono for bound in part.parts)
                    sophemes = match_keysymbols_to_chars(phono, part.ortho)
                    entry_parts.append(" ".join(str(sopheme) for sopheme in sophemes))
                    
                return self.translation + " = " + " ".join(entry_parts)

        def affix_full_varname(affix: Affix):
            # if len(affixes_by_name[affix.is_suffix, affix.name]) == 1:
            #     return affix.varname
            return f"{affix.varname}:{ids_by_affix[affix.as_dict_key()]}"


        prefixes_dict: dict[AffixKey, tuple[Affix, tuple[Sopheme, ...]]] = {}
        suffixes_dict: dict[AffixKey, tuple[Affix, tuple[Sopheme, ...]]] = {}
        entries_list: list[Entry] = []

        affixes_by_name: dict[tuple[bool, str], list[Affix]] = defaultdict(list)
        ids_by_affix: dict[AffixKey, int] = {}

        with open(root / args.in_unilex_path, "r", encoding="utf-8") as file:
            n_entries_parsed = 0
            while len(line := file.readline()) > 0:
                if n_entries_parsed % 1000 == 0:
                    print(f"Parsed {n_entries_parsed}")
                n_entries_parsed += 1


                try:
                    translation, _, _, transcription, morphology, _ = line.split(":")

                    morphology_parts = split_morphology(transcription, morphology)
                    morphology_parts = match_morphology_to_chars(morphology_parts, translation)

                    ignore_entry = False
                    for part in morphology_parts:
                        if isinstance(part, Affix) and not part.is_suffix and part.as_dict_key() not in prefixes_dict:
                            prefixes_dict[part.as_dict_key()] = part, match_keysymbols_to_chars(part.phono, part.ortho)
                        if isinstance(part, Affix) and part.is_suffix and part.as_dict_key() not in suffixes_dict:
                            suffixes_dict[part.as_dict_key()] = part, match_keysymbols_to_chars(part.phono, part.ortho)
                        if isinstance(part, Affix) and part.as_dict_key() not in ids_by_affix:
                            affix_id = len(affixes_by_name[part.is_suffix, part.name]) + 1

                            affixes_by_name[part.is_suffix, part.name].append(part)
                            ids_by_affix[part.as_dict_key()] = affix_id

                        if isinstance(part, Affix) and part.is_suffix and part.name in ("s", "ing", "ed", "'s"):
                            ignore_entry = True

                    if ignore_entry:
                        continue


                    # sophemes = match_keysymbols_to_chars(transcription, translation)
                    entries_list.append(Entry(translation, morphology_parts))

                except Exception as e:
                    import traceback
                    print(f"failed to add {line.strip()}: {e} ({''.join(traceback.format_tb(e.__traceback__))})")
                    pass


        with open(out_path, "w+", encoding="utf-8") as out_file:
            _ = out_file.write("[[meta]]\n")
            _ = out_file.write("hatchery_format_version = 0.0.0\n")


            _ = out_file.write("\n")
            _ = out_file.write("[[affixes]]\n")
            for prefix_key in sorted(prefixes_dict.keys(), key=lambda affix: (affix.name, ids_by_affix[affix])):
                prefix, sophemes = prefixes_dict[prefix_key]
                _ = out_file.write(affix_full_varname(prefix) + " = " + " ".join(str(sopheme) for sopheme in sophemes) + " ^\n")
            for suffix_key in sorted(suffixes_dict.keys(), key=lambda affix: (affix.name, ids_by_affix[affix])):
                suffix, sophemes = suffixes_dict[suffix_key]
                _ = out_file.write(affix_full_varname(suffix) + " = " + "^ " + " ".join(str(sopheme) for sopheme in sophemes) + "\n")

            n_entries_written = 0

            _ = out_file.write("\n")
            _ = out_file.write("[[entries]]\n")
            for entry in entries_list:
                if n_entries_written % 1000 == 0:
                    print(f"Written {n_entries_written}")
                n_entries_written += 1

                _ = out_file.write(str(entry) + "\n")
                    # sophemes_json.append(tuple(sopheme.to_dict() for sopheme in match_sophemes_to_chords(translation, transcription)))
                    # if translation not in reverse_lapwing_dict: continue

                    # for outline_steno in reverse_lapwing_dict[translation]:
                        # out_file.write(" ".join(str(sopheme) for sopheme in match_sophemes(translation, transcription, outline_steno)) + "\n")

                        # sophemes_json.append(tuple(sopheme.to_dict() for sopheme in match_sophemes(translation, transcription, outline_steno)))

                # json.dump(sophemes_json, out_file)

    print(f"Generating entries…")
    duration = timeit.timeit(generate, number=1)
    print(f"Finished (took {duration} s)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("-j", "--in-json-path", "--in-json", help="path to the input JSON dictionary", required=True)  
    parser.add_argument("-u", "--in-unilex-path", "--in-unilex", help="path to the input Unilex lexicon", required=True)
    parser.add_argument("-o", "--out-path", "--out", help="path to output the Hatchery dictionary (to use in Plover, use the `hatchery` file extension)", required=True)
    args = parser.parse_args()

    _setup_plover()  
    _main(args)