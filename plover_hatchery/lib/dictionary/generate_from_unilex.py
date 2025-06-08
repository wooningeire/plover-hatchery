from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator, Generic, TypeVar, final, overload

import toml

from plover_hatchery.lib.alignment.match_sophemes import match_keysymbols_to_chars
from plover_hatchery.lib.alignment.parse_morphology import AffixStressNormalizedKey, RootStressNormalizedKey, split_morphology, Affix, AffixKey, Formatting, Morpheme, MorphemeKey, MorphemeStressNormalizedKey, MorphemeSeq, Morphology, Root, RootKey
from plover_hatchery.lib.alignment.match_morphology import match_morphology_to_chars
from plover_hatchery.lib.dictionary.HatcheryDictionaryContents import HatcheryDictionaryContents
from plover_hatchery.lib.sopheme import Sopheme, Keysymbol

_Item = TypeVar("_Item")
_BaseKey = TypeVar("_BaseKey")
_NormalizedKey = TypeVar("_NormalizedKey")

@final
class _EntryTracker(Generic[_Item, _BaseKey, _NormalizedKey]):
    def __init__(self):
        self.normalized_keys: dict[_BaseKey, _NormalizedKey] = {}
        self.by_normalized_key: dict[_NormalizedKey, _Item] = {}
        self.by_name: dict[str, list[_Item]] = defaultdict(list)
        self.ids: dict[_NormalizedKey, int] = {}


    def register(self, item: _Item, name: str, key: _BaseKey, normalized_key: _NormalizedKey):
        self.normalized_keys[key] = normalized_key

        if normalized_key in self.by_normalized_key: return


        new_id = len(self.by_name[name]) + 1

        # self.n_uses[self.normalized_key] += 1
        self.by_normalized_key[normalized_key] = item
        self.by_name[name].append(item)
        self.ids[normalized_key] = new_id


    def id_from_base_key(self, key: _BaseKey):
        return self.ids[self.normalized_keys[key]]

    
    def base_keys(self):
        return self.normalized_keys.keys()



@dataclass(frozen=True)
class _FinalEntry:
    translation: str
    morphology: Morphology


@final
class _UnilexHatcheryConverter:
    def __init__(self):
        self.__morphemes: _EntryTracker[Morpheme, MorphemeKey, MorphemeStressNormalizedKey] = _EntryTracker()
        self.__roots: _EntryTracker[Root, RootKey, RootStressNormalizedKey] = _EntryTracker()
        self.__prefixes: _EntryTracker[Affix, AffixKey, AffixStressNormalizedKey] = _EntryTracker()
        self.__suffixes: _EntryTracker[Affix, AffixKey, AffixStressNormalizedKey] = _EntryTracker()


    def __affix_tracker_for(self, affix: Affix):
        if affix.is_prefix:
            return self.__prefixes
        return self.__suffixes 


    def __get_normalized_chunk_keysymbols(self, chunk: "Affix | Root") -> Generator[MorphemeStressNormalizedKey, None, None]:
        for part in chunk.morpheme_seq.parts:
            if isinstance(part, Formatting): continue

            yield self.__morphemes.normalized_keys[part.dict_key]
            

    @overload
    def __normalize_chunk_stress(self, chunk: Affix) -> AffixStressNormalizedKey: ...
    @overload
    def __normalize_chunk_stress(self, chunk: Root) -> RootStressNormalizedKey: ...
    def __normalize_chunk_stress(self, chunk: "Affix | Root"):
        max_stress = Keysymbol.max_stress_value(
            self.__morphemes.normalized_keys[morpheme.dict_key].max_stress
            for morpheme in chunk.morpheme_seq.parts
            if isinstance(morpheme, Morpheme)
        )

        morpheme_keys = tuple(self.__get_normalized_chunk_keysymbols(chunk))
        if isinstance(chunk, Affix):
            return AffixStressNormalizedKey(chunk.is_suffix, chunk.morpheme_seq.name, morpheme_keys, max_stress, chunk.morpheme_seq.ortho)
        
        return RootStressNormalizedKey(chunk.morpheme_seq.name, morpheme_keys, max_stress, chunk.morpheme_seq.ortho)


    def __root_full_varname(self, root: Root):
        if len(self.__roots.by_name[root.morpheme_seq.name]) == 1:
            return root.varname
        return f"{root.varname}:{self.__roots.id_from_base_key(root.dict_key)}"

    def __affix_full_varname(self, affix: Affix):
        if len(self.__affix_tracker_for(affix).by_name[affix.morpheme_seq.name]) == 1:
            return affix.varname
        return f"{affix.varname}:{self.__affix_tracker_for(affix).id_from_base_key(affix.dict_key)}"

    def __morpheme_full_varname(self, morpheme: Morpheme):
        if len(self.__morphemes.by_name[morpheme.name]) == 1:
            return morpheme.varname

        return f"{morpheme.varname}:{self.__morphemes.id_from_base_key(morpheme.dict_key)}"

    def __morpheme_seq_definition(self, morpheme_seq: MorphemeSeq, parent_max_stress: int):
        return " ".join(self.__syntax(morpheme, parent_max_stress) for morpheme in morpheme_seq.parts)

    def __morpheme_definition(self, morpheme: Morpheme):
        normalized_key = self.__morphemes.normalized_keys[morpheme.dict_key]
        sophemes = match_keysymbols_to_chars(normalized_key.phono, morpheme.ortho)
        return " ".join(str(sopheme) for sopheme in sophemes)

    def __morpheme_transclusion(self, morpheme: Morpheme, parent_max_stress: int):
        return (
            "{" + self.__morpheme_full_varname(morpheme) + "}"
            + self.__transclusion_stress_marker(
                self.__morphemes.normalized_keys[morpheme.dict_key].max_stress,
                parent_max_stress,
            )
        )

    def __affix_syntax(self, affix: Affix):
        return (
            "{" + self.__affix_full_varname(affix) + "}"
            + self.__transclusion_stress_marker(self.__affix_tracker_for(affix).normalized_keys[affix.dict_key].max_stress)
        )

    def __root_syntax(self, root: Root):
        return (
            "{" + self.__root_full_varname(root) + "}"
            + self.__transclusion_stress_marker(self.__roots.normalized_keys[root.dict_key].max_stress)
        )

    def __formatting_syntax(self, formatting: Formatting):
        return str(Sopheme(formatting.ortho, ()))

    def __syntax(self, part: "Morpheme | Formatting", parent_max_stress: int):
        if isinstance(part, Morpheme):
            return self.__morpheme_transclusion(part, parent_max_stress)
        
        return self.__formatting_syntax(part)

    def __transclusion_stress_marker(self, key_max_stress: int, parent_max_stress: int=1):
        if key_max_stress == 0:
            return ""

        return Keysymbol.stress_marker(key_max_stress - parent_max_stress + 1)

    def __final_entry_definition(self, entry: _FinalEntry):
        entry_parts: list[str] = []
        for chunk in entry.morphology.chunks:
            if isinstance(chunk, Formatting):
                entry_parts.append(self.__formatting_syntax(chunk))
                continue

            elif isinstance(chunk, Affix):
                entry_parts.append(self.__affix_syntax(chunk))
                continue

            else:
                entry_parts.append(self.__root_syntax(chunk))
                # if root_n_uses[root_key] > 1:
                #     entry_parts.append("{" + root_full_varname(chunk) + "}")
                # else:
                #     entry_parts.append(morpheme_seq_definition(chunk.morpheme_seq))

                continue
            
        return " ".join(entry_parts)


    def generate(self, in_path: Path, out_path: Path, failures_out_path: Path | None):
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



        entries_list: list[_FinalEntry] = []


        n_entries_parsed = 0

        failures_str = ""

        with open(in_path, "r", encoding="utf-8") as file:
            print()
            while len(line := file.readline()) > 0:
                if n_entries_parsed % 1000 == 0:
                    print(f"\x1b[FParsed {n_entries_parsed}")
                n_entries_parsed += 1


                try:
                    translation, _, _, transcription, morphology_str, _ = line.split(":")


                    morphology = split_morphology(transcription, morphology_str)
                    morphology = match_morphology_to_chars(morphology, translation)

                    for part in morphology.parts:
                        if not isinstance(part, Morpheme): continue

                        keysymbols = Keysymbol.parse_seq(part.phono)
                        new_keysymbols, max_stress = Keysymbol.normalize_stress(keysymbols)
                        normalized_key = MorphemeStressNormalizedKey(part.name, new_keysymbols, max_stress, part.ortho)

                        self.__morphemes.register(part, part.name, part.dict_key, normalized_key)



                    ignore_entry = False
                    for chunk in morphology.chunks:
                        if isinstance(chunk, Formatting): continue
                            
                        if isinstance(chunk, Affix):
                            normalized_key = self.__normalize_chunk_stress(chunk)
                            self.__affix_tracker_for(chunk).register(chunk, chunk.morpheme_seq.name, chunk.dict_key, normalized_key)

                            if chunk.is_suffix and chunk.morpheme_seq.name in ("s", "ing", "ed", "'s"):
                                ignore_entry = True

                            continue

                        normalized_key = self.__normalize_chunk_stress(chunk)
                        self.__roots.register(chunk, chunk.morpheme_seq.name, chunk.dict_key, normalized_key)


                    if ignore_entry:
                        continue


                    # sophemes = match_keysymbols_to_chars(transcription, translation)
                    entries_list.append(_FinalEntry(translation, morphology))

                except Exception as e:
                    import traceback
                    if failures_out_path is not None:
                        failures_str += line
                        # print(f"failed {line.strip()}: {e} ({''.join(traceback.format_tb(e.__traceback__))})")



        if failures_out_path is not None and len(failures_str) > 0:
            with open(failures_out_path, "r", encoding="utf-8") as failures_file:
                _ = failures_file.write(failures_str)
            

        out_dict: HatcheryDictionaryContents = {
            "meta": {
                "hatchery-format-version": "0.0.0",
            },
            "morphemes": {},
            "entries": {},
        }


        for _, morpheme in sorted(self.__morphemes.by_normalized_key.items(), key=lambda item: (item[0].name, self.__morphemes.ids[item[0]])):
            # if morpheme_n_uses[morpheme_key] == 1: continue
            out_dict["morphemes"][self.__morpheme_full_varname(morpheme)] = self.__morpheme_definition(morpheme)

        for root_key, root in sorted(self.__roots.by_normalized_key.items(), key=lambda item: (item[0].name, self.__roots.ids[item[0]])):
            # if root_n_uses[root_key] == 1: continue
            out_dict["morphemes"][self.__root_full_varname(root)] = self.__morpheme_seq_definition(root.morpheme_seq, root_key.max_stress)

        for prefix_key, prefix in sorted(self.__prefixes.by_normalized_key.items(), key=lambda item: (item[0].name, self.__prefixes.ids[item[0]])):
            out_dict["morphemes"][self.__affix_full_varname(prefix)] = self.__morpheme_seq_definition(prefix.morpheme_seq, prefix_key.max_stress)

        for suffix_key, suffix in sorted(self.__suffixes.by_normalized_key.items(), key=lambda item: (item[0].name, self.__suffixes.ids[item[0]])):
            out_dict["morphemes"][self.__affix_full_varname(suffix)] = self.__morpheme_seq_definition(suffix.morpheme_seq, suffix_key.max_stress)


        print()
        n_entries_written = 0
        for entry in entries_list:
            if n_entries_written % 1000 == 0:
                print(f"\x1b[FWritten {n_entries_written}")
            n_entries_written += 1

            out_dict["entries"][entry.translation] = self.__final_entry_definition(entry)
            

        with open(out_path, "w+", encoding="utf-8") as out_file:
            toml.dump(out_dict, out_file)

def generate_from_unilex(in_path: Path, out_path: Path, failures_out_path: Path | None):
    return _UnilexHatcheryConverter().generate(in_path, out_path, failures_out_path)