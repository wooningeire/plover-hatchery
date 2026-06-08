import json
import re
from pathlib import Path
from typing import Any

import toml

from plover_hatchery.Store import store
from plover_hatchery.lib.dictionary.HatcheryDictionaryContents import HatcheryDictionaryContents
from plover_hatchery.lib.dictionary.read import read_hatchery_dictionary
from plover_hatchery.lib.sopheme import parse_entry_definition
from plover_hatchery_lib_rs import DefDict, DefView


HATCHERY_FORMAT_VERSION = "0.0.0"
DEFAULT_ENTRY_PAGE_LIMIT = 100
MAX_ENTRY_PAGE_LIMIT = 200


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


def list_hatchery_dictionary_entries(
    *,
    dictionary_path: Any,
    offset: Any=None,
    limit: Any=None,
    query: Any=None,
    resolve_translations: Any=None,
):
    dictionary_path, _dictionary = _loaded_dictionary(dictionary_path)
    offset = _optional_nonnegative_int(offset, "offset", default=0)
    limit = _optional_page_limit(limit)
    query = _optional_string(query, "query").strip()
    resolve_translations = _optional_bool(resolve_translations, default=False)

    contents = _read_dictionary_contents(dictionary_path)
    morphemes = _required_dict_section(contents, "morphemes")
    entries = _optional_dict_section(contents, "entries")
    page_entries, total_count = _entry_page(
        entries=entries,
        offset=offset,
        limit=limit,
        query=query,
    )

    return {
        "dictionary": {
            "path": dictionary_path,
            "label": Path(dictionary_path).name or dictionary_path,
        },
        "stats": {
            "morphemeCount": len(morphemes),
            "entryCount": len(entries),
            "definitionCount": len(morphemes) + len(entries),
        },
        "entries": [
            _entry_summary(
                contents,
                key,
                str(definition).strip(),
                resolve_translation=resolve_translations,
            )
            for key, definition in page_entries
        ],
        "pagination": {
            "offset": offset,
            "limit": limit,
            "totalCount": total_count,
            "returnedCount": len(page_entries),
            "hasPrevious": offset > 0,
            "hasNext": offset + len(page_entries) < total_count,
            "query": query,
        },
    }


def add_entry_to_hatchery_dictionary(
    *,
    dictionary_path: Any,
    translation: Any,
    definition: Any,
):
    dictionary_path, dictionary = _loaded_dictionary(dictionary_path)
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

    return {
        "entry": {
            "key": entry_key,
            "translation": translation,
            "definition": definition,
        },
        "compile": _compile_changed_dictionary(dictionary_path, dictionary),
    }


def delete_entry_from_hatchery_dictionary(
    *,
    dictionary_path: Any,
    entry_key: Any,
):
    dictionary_path, dictionary = _loaded_dictionary(dictionary_path)
    entry_key = _required_string(entry_key, "entryKey").strip()
    if entry_key == "":
        raise AddEntryValidationError("entryKey is required")

    contents = _read_dictionary_contents(dictionary_path)
    entries = _optional_dict_section(contents, "entries")
    if entry_key not in entries:
        raise AddEntryValidationError("Entry is not present")

    definition = str(entries[entry_key]).strip()
    translation = _resolve_entry_translation(contents, entry_key, definition)

    _delete_entry_line(Path(dictionary_path), entry_key)

    return {
        "entry": {
            "key": entry_key,
            "translation": translation,
            "definition": definition,
        },
        "compile": _compile_changed_dictionary(dictionary_path, dictionary),
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


def _loaded_dictionary(dictionary_path: Any):
    dictionary_path = _required_string(dictionary_path, "dictionaryPath")
    dictionary = store.hatchery_dictionaries.get(dictionary_path)
    if dictionary is None:
        raise UnknownHatcheryDictionaryError("Hatchery dictionary is not loaded")

    return dictionary_path, dictionary


def _compile_changed_dictionary(dictionary_path: str, dictionary: Any):
    invalidate_lookup_cache = getattr(dictionary, "invalidate_lookup_cache", None)
    if callable(invalidate_lookup_cache):
        invalidate_lookup_cache()

    compile_result = dictionary.compile(refresh_cache=False)
    if not isinstance(compile_result, dict):
        compile_result = {"status": str(compile_result)}

    return {
        "path": dictionary_path,
        **compile_result,
    }


def _required_string(value: Any, field_name: str):
    if not isinstance(value, str):
        raise AddEntryValidationError(f"{field_name} must be a string")

    return value


def _optional_string(value: Any, field_name: str):
    if value is None:
        return ""

    if not isinstance(value, str):
        raise AddEntryValidationError(f"{field_name} must be a string")

    return value


def _optional_nonnegative_int(value: Any, field_name: str, *, default: int):
    if value is None or value == "":
        return default

    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        raise AddEntryValidationError(f"{field_name} must be a non-negative integer")

    if parsed_value < 0:
        raise AddEntryValidationError(f"{field_name} must be a non-negative integer")

    return parsed_value


def _optional_page_limit(value: Any):
    limit = _optional_nonnegative_int(
        value,
        "limit",
        default=DEFAULT_ENTRY_PAGE_LIMIT,
    )

    if limit == 0:
        raise AddEntryValidationError("limit must be greater than 0")

    return min(limit, MAX_ENTRY_PAGE_LIMIT)


def _optional_bool(value: Any, *, default: bool):
    if value is None or value == "":
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized_value = value.strip().lower()
        if normalized_value in {"1", "true", "yes", "on"}:
            return True
        if normalized_value in {"0", "false", "no", "off"}:
            return False

    raise AddEntryValidationError("resolveTranslations must be a boolean")


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


def _entry_page(
    *,
    entries: dict[str, Any],
    offset: int,
    limit: int,
    query: str,
):
    normalized_query = query.lower()
    page_entries: list[tuple[str, Any]] = []
    total_count = 0

    for key, definition in entries.items():
        if not _entry_matches_query(key, definition, normalized_query):
            continue

        if offset <= total_count < offset + limit:
            page_entries.append((key, definition))

        total_count += 1

    return page_entries, total_count


def _entry_matches_query(key: str, definition: Any, normalized_query: str):
    if normalized_query == "":
        return True

    return (
        normalized_query in key.lower()
        or normalized_query in str(definition).lower()
    )


def _entry_summary(
    contents: HatcheryDictionaryContents,
    entry_key: str,
    definition: str,
    *,
    resolve_translation: bool,
):
    return {
        "key": entry_key,
        "translation": _resolve_entry_translation(contents, entry_key, definition)
            if resolve_translation
            else None,
        "definition": definition,
    }


def _resolve_entry_translation(
    contents: HatcheryDictionaryContents,
    entry_key: str,
    definition: str,
):
    try:
        return _resolve_definition_translation(contents, entry_key, _parse_definition(definition))
    except AddEntryValidationError:
        return None


def _resolve_definition_translation(
    contents: HatcheryDictionaryContents,
    entry_key: str,
    entities: list[Any],
):
    defs = DefDict()

    for varname, definition in _definition_items(contents):
        if varname == entry_key:
            continue

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


def _delete_entry_line(path: Path, entry_key: str):
    try:
        text = path.read_text(encoding="utf-8")
        next_text, removed = _remove_entry_line(text, entry_key)
        if not removed:
            raise AddEntryValidationError("Could not find entry line to delete")

        path.write_text(next_text, encoding="utf-8")
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


def _remove_entry_line(text: str, entry_key: str):
    lines = text.splitlines(keepends=True)

    entries_header_index = None
    for index, line in enumerate(lines):
        header_match = _TABLE_HEADER_RE.match(line.rstrip("\r\n"))
        if header_match is not None and header_match.group(1).strip() == "entries":
            entries_header_index = index
            break

    if entries_header_index is None:
        return text, False

    for index in range(entries_header_index + 1, len(lines)):
        if _TABLE_HEADER_RE.match(lines[index].rstrip("\r\n")) is not None:
            break

        if _entry_line_key(lines[index]) == entry_key:
            return "".join([
                *lines[:index],
                *lines[index + 1:],
            ]), True

    return text, False


def _entry_line_key(line: str):
    try:
        parsed_line = toml.loads(f"[entries]\n{line}")
    except toml.TomlDecodeError:
        return None

    entries = parsed_line.get("entries")
    if not isinstance(entries, dict) or len(entries) != 1:
        return None

    return next(iter(entries.keys()))
