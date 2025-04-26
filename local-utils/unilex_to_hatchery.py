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

from plover_hatchery.lib.alignment.parse_morphology import AffixKey, Formatting, Morpheme, MorphemeKey, MorphemeSeq, Morphology, Root, RootKey




def _setup_plover():
    registry.update()
    system.setup(DEFAULT_SYSTEM_NAME)



def _main(args: argparse.Namespace):
    from plover_hatchery.lib.alignment.match_sophemes import match_keysymbols_to_chars
    from plover_hatchery.lib.alignment.parse_morphology import split_morphology, Affix
    from plover_hatchery.lib.alignment.match_morphology import match_morphology_to_chars
    from plover_hatchery.lib.sopheme import Sopheme


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
            morphology: Morphology

            def __str__(self):
                entry_parts: list[str] = []
                for chunk in self.morphology.chunks:
                    if isinstance(chunk, Formatting):
                        entry_parts.append(formatting_code(chunk))
                        continue

                    elif isinstance(chunk, Affix):
                        entry_parts.append("{" + affix_full_varname(chunk) + "}")
                        continue

                    else:
                        entry_parts.append("{" + root_full_varname(chunk) + "}")
                        # if root_n_uses[root_key] > 1:
                        #     entry_parts.append("{" + root_full_varname(chunk) + "}")
                        # else:
                        #     entry_parts.append(morpheme_seq_definition(chunk.morpheme_seq))

                        continue
                    
                return self.translation + " = " + " ".join(entry_parts)

        def root_full_varname(root: Root):
            if len(roots_by_name[root.morpheme_seq.name]) == 1:
                return root.varname
            return f"{root.varname}:{root_ids_by_root[root.dict_key]}"

        def affix_full_varname(affix: Affix):
            if len(affixes_by_name[affix.is_suffix, affix.morpheme_seq.name]) == 1:
                return affix.varname
            return f"{affix.varname}:{affix_ids_by_affix[affix.dict_key]}"

        def morpheme_full_varname(morpheme: Morpheme):
            if len(morphemes_by_name[morpheme.name]) == 1:
                return morpheme.varname
            return f"{morpheme.varname}:{morpheme_ids_by_morpheme[morpheme.dict_key]}"

        def morpheme_seq_definition(morpheme_seq: MorphemeSeq):
            return " ".join(code(morpheme) for morpheme in morpheme_seq.parts)

        def morpheme_definition(morpheme: Morpheme):
            sophemes = match_keysymbols_to_chars(morpheme.phono, morpheme.ortho)
            return " ".join(str(sopheme) for sopheme in sophemes)

        def morpheme_code(morpheme: Morpheme):
            return "{" + morpheme_full_varname(morpheme) + "}"
            # if morpheme_n_uses[morpheme.dict_key] > 1:
            #     return "{" + morpheme_full_varname(morpheme) + "}"
            
            # return morpheme_definition(morpheme)

        def formatting_code(formatting: Formatting):
            return str(Sopheme(formatting.ortho, ()))

        def code(part: "Morpheme | Formatting"):
            if isinstance(part, Morpheme):
                return morpheme_code(part)
            
            return formatting_code(part)


        morphemes_dict: dict[MorphemeKey, Morpheme] = {}
        morphemes_by_name: dict[str, list[Morpheme]] = defaultdict(list)
        morpheme_ids_by_morpheme: dict[MorphemeKey, int] = {}
        # morpheme_n_uses: dict[MorphemeKey, int] = defaultdict(lambda: 0)


        roots_dict: dict[RootKey, Root] = {}
        roots_by_name: dict[str, list[Root]] = defaultdict(list)
        root_ids_by_root: dict[RootKey, int] = {}
        # root_n_uses: dict[RootKey, int] = defaultdict(lambda: 0)


        prefixes_dict: dict[AffixKey, Affix] = {}
        suffixes_dict: dict[AffixKey, Affix] = {}
        entries_list: list[Entry] = []

        affixes_by_name: dict[tuple[bool, str], list[Affix]] = defaultdict(list)
        affix_ids_by_affix: dict[AffixKey, int] = {}

        with open(root / args.in_unilex_path, "r", encoding="utf-8") as file:
            n_entries_parsed = 0
            while len(line := file.readline()) > 0:
                if n_entries_parsed % 1000 == 0:
                    print(f"Parsed {n_entries_parsed}")
                n_entries_parsed += 1


                try:
                    translation, _, _, transcription, morphology, _ = line.split(":")


                    morphology = split_morphology(transcription, morphology)
                    morphology = match_morphology_to_chars(morphology, translation)

                    for part in morphology.parts:
                        if not isinstance(part, Morpheme): continue

                        # morpheme_n_uses[part.dict_key] += 1
                        if part.dict_key in morphemes_dict: continue


                        morpheme_id = len(morphemes_by_name[part.name]) + 1

                        morphemes_dict[part.dict_key] = part
                        morphemes_by_name[part.name].append(part)
                        morpheme_ids_by_morpheme[part.dict_key] = morpheme_id



                    ignore_entry = False
                    for chunk in morphology.chunks:
                        if isinstance(chunk, Affix):
                            if not chunk.is_suffix and chunk.dict_key not in prefixes_dict:
                                prefixes_dict[chunk.dict_key] = chunk
                            if chunk.is_suffix and chunk.dict_key not in suffixes_dict:
                                suffixes_dict[chunk.dict_key] = chunk
                            if chunk.dict_key not in affix_ids_by_affix:
                                affix_id = len(affixes_by_name[chunk.is_suffix, chunk.morpheme_seq.name]) + 1

                                affixes_by_name[chunk.is_suffix, chunk.morpheme_seq.name].append(chunk)
                                affix_ids_by_affix[chunk.dict_key] = affix_id

                            if chunk.is_suffix and chunk.morpheme_seq.name in ("s", "ing", "ed", "'s"):
                                ignore_entry = True

                            continue

                        elif isinstance(chunk, Root):
                            # root_n_uses[chunk.dict_key] += 1
                            if chunk.dict_key in roots_dict: continue


                            root_id = len(roots_by_name[chunk.morpheme_seq.name]) + 1

                            roots_dict[chunk.dict_key] = chunk
                            roots_by_name[chunk.morpheme_seq.name].append(chunk)
                            root_ids_by_root[chunk.dict_key] = root_id


                    if ignore_entry:
                        continue


                    # sophemes = match_keysymbols_to_chars(transcription, translation)
                    entries_list.append(Entry(translation, morphology))

                except Exception as e:
                    import traceback
                    print(f"failed to add {line.strip()}: {e} ({''.join(traceback.format_tb(e.__traceback__))})")
                    pass


        with open(out_path, "w+", encoding="utf-8") as out_file:
            _ = out_file.write("[meta]\n")
            _ = out_file.write("hatchery_format_version = 0.0.0\n")


            _ = out_file.write("\n")
            _ = out_file.write("[morphemes]\n")

            for morpheme_key in sorted(morphemes_dict.keys(), key=lambda morpheme: (morpheme.name, morpheme_ids_by_morpheme[morpheme])):
                # if morpheme_n_uses[morpheme_key] == 1: continue

                morpheme = morphemes_dict[morpheme_key]
                _ = out_file.write(morpheme_full_varname(morpheme) + " = " + morpheme_definition(morpheme) + "\n")


            _ = out_file.write("\n")
            _ = out_file.write("[roots]\n")

            for root_key in sorted(roots_dict.keys(), key=lambda root: (root.name, root_ids_by_root[root])):
                # if root_n_uses[root_key] == 1: continue

                root_chunk = roots_dict[root_key]
                _ = out_file.write(root_full_varname(root_chunk) + " = " + morpheme_seq_definition(root_chunk.morpheme_seq) + "\n")


            _ = out_file.write("\n")
            _ = out_file.write("[affixes]\n")

            for prefix_key in sorted(prefixes_dict.keys(), key=lambda affix: (affix.name, affix_ids_by_affix[affix])):
                prefix = prefixes_dict[prefix_key]
                _ = out_file.write(affix_full_varname(prefix) + " = " + morpheme_seq_definition(prefix.morpheme_seq) + " ^\n")

            for suffix_key in sorted(suffixes_dict.keys(), key=lambda affix: (affix.name, affix_ids_by_affix[affix])):
                suffix = suffixes_dict[suffix_key]
                _ = out_file.write(affix_full_varname(suffix) + " = ^ " + morpheme_seq_definition(suffix.morpheme_seq) + "\n")


            n_entries_written = 0

            _ = out_file.write("\n")
            _ = out_file.write("[entries]\n")
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