import json
import re
from pathlib import Path
from typing import Any

from plover_hatchery.Store import store
from plover_hatchery.lib.dictionary.HatcheryDictionaryContents import HatcheryDictionaryContents
from plover_hatchery.lib.dictionary.read import read_hatchery_dictionary
from plover_hatchery.lib.sopheme import parse_entry_definition
from plover_hatchery_lib_rs import DefDict, DefView


HATCHERY_FORMAT_VERSION = "0.0.0"


class AddEntryValidationError(ValueError):
    pass


class UnknownHatcheryDictionaryError(Exception):
    pass


def hatchery_dictionary_summaries():
    return [
        {
            "path": path,
            "label": Path(path).name or path,
        }
        for path in store.hatchery_dictionaries.keys()
    ]


def add_entry_to_hatchery_dictionary(
    *,
    dictionary_path: Any,
    translation: Any,
    definition: Any,
):
    dictionary = store.hatchery_dictionaries.get(_required_string(dictionary_path, "dictionaryPath"))
    if dictionary is None:
        raise UnknownHatcheryDictionaryError("Hatchery dictionary is not loaded")

    translation = _required_string(translation, "translation").strip()
    definition = _required_string(definition, "definition").strip()
    if translation == "":
        raise AddEntryValidationError("Translation is required")
    if definition == "":
        raise AddEntryValidationError("Definition is required")

    contents = _read_dictionary_contents(dictionary_path)
    morphemes = _required_dict_section(contents, "morphemes")
    entries = _optional_dict_section(contents, "entries")

    entry_key = unique_entry_key(translation, set(morphemes.keys()) | set(entries.keys()))
    entities = _parse_definition(definition)
    resolved_translation = _resolve_definition_translation(contents, entry_key, entities)
    if resolved_translation != translation:
        raise AddEntryValidationError(
            f'Definition resolves to "{resolved_translation}", not "{translation}"'
        )

    _append_entry_line(Path(dictionary_path), entry_key, definition)

    invalidate_lookup_cache = getattr(dictionary, "invalidate_lookup_cache", None)
    if callable(invalidate_lookup_cache):
        invalidate_lookup_cache()

    compile_result = dictionary.compile(refresh_cache=False)
    if not isinstance(compile_result, dict):
        compile_result = {"status": str(compile_result)}
    compile_result = {
        "path": dictionary_path,
        **compile_result,
    }

    return {
        "entry": {
            "key": entry_key,
            "translation": translation,
            "definition": definition,
        },
        "compile": compile_result,
    }


def unique_entry_key(translation: str, existing_keys: set[str]):
    stem = safe_entry_key_stem(translation)
    candidate = stem
    index = 2

    while candidate in existing_keys:
        candidate = f"{stem}:{index}"
        index += 1

    return candidate


def safe_entry_key_stem(translation: str):
    pieces: list[str] = []
    last_was_separator = False

    for char in translation.strip().lower():
        if char.isalnum() or char in {"-", "'"}:
            pieces.append(char)
            last_was_separator = False
            continue

        if not last_was_separator:
            pieces.append("-")
            last_was_separator = True

    stem = "".join(pieces).strip("-'")
    if stem == "":
        return "entry"

    return stem


def _required_string(value: Any, field_name: str):
    if not isinstance(value, str):
        raise AddEntryValidationError(f"{field_name} must be a string")

    return value


def _read_dictionary_contents(dictionary_path: str):
    try:
        contents = read_hatchery_dictionary(dictionary_path)
    except AssertionError:
        raise AddEntryValidationError(
            f"Hatchery format version must be {HATCHERY_FORMAT_VERSION}"
        )
    except Exception as error:
        raise AddEntryValidationError(f"Could not read Hatchery dictionary: {error}")

    return contents


def _required_dict_section(contents: HatcheryDictionaryContents, section_name: str):
    section = dict(contents).get(section_name)
    if not isinstance(section, dict):
        raise AddEntryValidationError(f'[{section_name}] must be present')

    return section


def _optional_dict_section(contents: HatcheryDictionaryContents, section_name: str):
    section = dict(contents).get(section_name, {})
    if not isinstance(section, dict):
        raise AddEntryValidationError(f'[{section_name}] must be a table')

    return section


def _definition_items(contents: HatcheryDictionaryContents):
    morphemes = _required_dict_section(contents, "morphemes")
    entries = _optional_dict_section(contents, "entries")

    yield from morphemes.items()
    yield from entries.items()


def _parse_definition(definition: str):
    try:
        return list(parse_entry_definition(definition))
    except ValueError as error:
        raise AddEntryValidationError(f"Definition could not be parsed: {error}")


def _resolve_definition_translation(
    contents: HatcheryDictionaryContents,
    entry_key: str,
    entities: list[Any],
):
    defs = DefDict()

    for varname, definition in _definition_items(contents):
        try:
            defs.add(varname, list(parse_entry_definition(str(definition).strip())))
        except ValueError:
            continue

    defs.add(entry_key, entities)

    try:
        return DefView(defs, defs.get_def(entry_key)).translation()
    except Exception as error:
        raise AddEntryValidationError(f"Definition could not be resolved: {error}")


def _append_entry_line(path: Path, entry_key: str, definition: str):
    entry_line = f"{_toml_basic_string(entry_key)} = {_toml_basic_string(definition)}"

    try:
        text = path.read_text(encoding="utf-8")
        path.write_text(_insert_entry_line(text, entry_line), encoding="utf-8")
    except OSError as error:
        raise RuntimeError(f"Could not write Hatchery dictionary: {error}")


def _toml_basic_string(value: str):
    return json.dumps(value, ensure_ascii=False)


_TABLE_HEADER_RE = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?$")


def _insert_entry_line(text: str, entry_line: str):
    newline = "\r\n" if "\r\n" in text else "\n"
    inserted_line = f"{entry_line}{newline}"
    lines = text.splitlines(keepends=True)

    entries_header_index = None
    for index, line in enumerate(lines):
        header_match = _TABLE_HEADER_RE.match(line.rstrip("\r\n"))
        if header_match is not None and header_match.group(1).strip() == "entries":
            entries_header_index = index
            break

    if entries_header_index is None:
        prefix = text
        if prefix != "" and not prefix.endswith(("\n", "\r")):
            prefix += newline
        if prefix != "" and not prefix.endswith(f"{newline}{newline}"):
            prefix += newline

        return f"{prefix}[entries]{newline}{inserted_line}"

    insert_index = len(lines)
    for index in range(entries_header_index + 1, len(lines)):
        if _TABLE_HEADER_RE.match(lines[index].rstrip("\r\n")) is not None:
            insert_index = index
            break

    if insert_index > 0 and not lines[insert_index - 1].endswith(("\n", "\r")):
        lines[insert_index - 1] += newline

    lines.insert(insert_index, inserted_line)

    return "".join(lines)
