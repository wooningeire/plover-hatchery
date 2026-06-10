import json
import re
from pathlib import Path
from typing import Any, Iterable

import toml

from plover_hatchery.Store import store
from plover_hatchery.lib.dictionary.HatcheryDictionaryContents import HatcheryDictionaryContents
from plover_hatchery.lib.dictionary.read import (
    ENTRY_FORMAT_SOPHEMES,
    ENTRY_FORMAT_THEORY_SYMBOLS,
    HatcheryEntry,
    SUPPORTED_HATCHERY_FORMAT_VERSIONS,
    all_entries,
    entry_items,
    normalize_entry,
    read_hatchery_dictionary,
)
from plover_hatchery.lib.sopheme import parse_entry_definition
from plover_hatchery_lib_rs import DefDict, DefView


DEFAULT_ENTRY_PAGE_LIMIT = 100
MAX_ENTRY_PAGE_LIMIT = 200
ADDABLE_ENTRY_FORMATS = {
    ENTRY_FORMAT_SOPHEMES,
    ENTRY_FORMAT_THEORY_SYMBOLS,
}


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
        entries=entry_items(contents),
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
                entry,
                resolve_translation=resolve_translations,
            )
            for entry in page_entries
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
    entry_format: Any=None,
):
    dictionary_path, dictionary = _loaded_dictionary(dictionary_path)
    translation = _required_string(translation, "translation").strip()
    definition = _required_string(definition, "definition").strip()
    entry_format = _optional_entry_format(entry_format)
    if translation == "":
        raise AddEntryValidationError("Translation is required")
    if definition == "":
        raise AddEntryValidationError("Definition is required")

    contents = _read_dictionary_contents(dictionary_path)
    morphemes = _required_dict_section(contents, "morphemes")
    entries = _optional_dict_section(contents, "entries")

    entry_key = unique_entry_key(translation, set(morphemes.keys()) | set(entries.keys()))
    if entry_format == ENTRY_FORMAT_SOPHEMES:
        entities = _parse_definition(definition)
        resolved_translation = _resolve_definition_translation(contents, entry_key, entities)
        if resolved_translation != translation:
            raise AddEntryValidationError(
                f'Definition resolves to "{resolved_translation}", not "{translation}"'
            )

        _append_entry_line(Path(dictionary_path), entry_key, definition)
    elif entry_format == ENTRY_FORMAT_THEORY_SYMBOLS:
        _append_entry_object(
            Path(dictionary_path),
            entry_key=entry_key,
            entry_format=entry_format,
            definition_field="theory-symbols",
            definition=definition,
            translation=translation,
        )
    else:
        raise AddEntryValidationError(f'Unsupported entry format "{entry_format}"')

    return {
        "entry": {
            "key": entry_key,
            "format": entry_format,
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

    entry = normalize_entry(entry_key, entries[entry_key])
    translation = _resolve_entry_translation(contents, entry)

    _delete_entry_line(Path(dictionary_path), entry_key)

    return {
        "entry": {
            "key": entry_key,
            "translation": translation,
            "definition": entry.definition,
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


def _optional_entry_format(value: Any):
    if value is None:
        return ENTRY_FORMAT_SOPHEMES

    entry_format = _required_string(value, "format").strip()
    if entry_format in ADDABLE_ENTRY_FORMATS:
        return entry_format

    addable_formats = ", ".join(sorted(ADDABLE_ENTRY_FORMATS))
    raise AddEntryValidationError(f"format must be one of {addable_formats}")


def _read_dictionary_contents(dictionary_path: str):
    try:
        contents = read_hatchery_dictionary(dictionary_path)
    except AssertionError:
        supported_versions = ", ".join(sorted(SUPPORTED_HATCHERY_FORMAT_VERSIONS))
        raise AddEntryValidationError(
            f"Hatchery format version must be one of {supported_versions}"
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
    yield from all_entries(contents)


def _parse_definition(definition: str):
    try:
        return list(parse_entry_definition(definition))
    except ValueError as error:
        raise AddEntryValidationError(f"Definition could not be parsed: {error}")


def _entry_page(
    *,
    entries: Iterable[HatcheryEntry],
    offset: int,
    limit: int,
    query: str,
):
    normalized_query = query.lower()
    page_entries: list[HatcheryEntry] = []
    total_count = 0

    for entry in entries:
        if not _entry_matches_query(entry, normalized_query):
            continue

        if offset <= total_count < offset + limit:
            page_entries.append(entry)

        total_count += 1

    return page_entries, total_count


def _entry_matches_query(entry: HatcheryEntry, normalized_query: str):
    if normalized_query == "":
        return True

    return (
        normalized_query in entry.key.lower()
        or normalized_query in entry.definition.lower()
        or (
            entry.translation is not None
            and normalized_query in entry.translation.lower()
        )
    )


def _entry_summary(
    contents: HatcheryDictionaryContents,
    entry: HatcheryEntry,
    *,
    resolve_translation: bool,
):
    return {
        "key": entry.key,
        "format": entry.format,
        "translation": _entry_summary_translation(
            contents,
            entry,
            resolve_translation=resolve_translation,
        ),
        "definition": entry.definition,
    }


def _entry_summary_translation(
    contents: HatcheryDictionaryContents,
    entry: HatcheryEntry,
    *,
    resolve_translation: bool,
):
    if entry.translation is not None:
        return entry.translation

    if not resolve_translation:
        return None

    return _resolve_entry_translation(contents, entry)


def _resolve_entry_translation(
    contents: HatcheryDictionaryContents,
    entry: HatcheryEntry,
):
    try:
        return _resolve_definition_translation(
            contents,
            entry.key,
            _parse_definition(entry.definition),
        )
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


def _append_entry_object(
    path: Path,
    *,
    entry_key: str,
    entry_format: str,
    definition_field: str,
    definition: str,
    translation: str,
):
    entry_object = "\n".join([
        f"[entries.{_toml_basic_string(entry_key)}]",
        f"format = {_toml_basic_string(entry_format)}",
        f"translation = {_toml_basic_string(translation)}",
        f"{definition_field} = {_toml_basic_string(definition)}",
    ])

    try:
        text = path.read_text(encoding="utf-8")
        path.write_text(_insert_entry_object(text, entry_object), encoding="utf-8")
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


def _insert_entry_object(text: str, entry_object: str):
    newline = "\r\n" if "\r\n" in text else "\n"
    normalized_entry_object = entry_object.replace("\n", newline)
    inserted_text = f"{normalized_entry_object}{newline}"
    lines = text.splitlines(keepends=True)

    entries_region_start = None
    entries_region_end = len(lines)
    for index, line in enumerate(lines):
        header_match = _TABLE_HEADER_RE.match(line.rstrip("\r\n"))
        if header_match is None:
            continue

        header_name = header_match.group(1).strip()
        is_entries_header = (
            header_name == "entries"
            or header_name.startswith("entries.")
        )

        if entries_region_start is None:
            if is_entries_header:
                entries_region_start = index
            continue

        if not is_entries_header:
            entries_region_end = index
            break

    if entries_region_start is None:
        prefix = text
        if prefix != "" and not prefix.endswith(("\n", "\r")):
            prefix += newline
        if prefix != "" and not prefix.endswith(f"{newline}{newline}"):
            prefix += newline

        return f"{prefix}{inserted_text}"

    if entries_region_end > 0 and not lines[entries_region_end - 1].endswith(("\n", "\r")):
        lines[entries_region_end - 1] += newline

    if entries_region_end > 0 and lines[entries_region_end - 1].strip() != "":
        inserted_text = f"{newline}{inserted_text}"

    lines.insert(entries_region_end, inserted_text)

    return "".join(lines)


def _remove_entry_line(text: str, entry_key: str):
    lines = text.splitlines(keepends=True)

    entries_header_index = None
    for index, line in enumerate(lines):
        header_match = _TABLE_HEADER_RE.match(line.rstrip("\r\n"))
        if header_match is not None and header_match.group(1).strip() == "entries":
            entries_header_index = index
            break

    if entries_header_index is not None:
        for index in range(entries_header_index + 1, len(lines)):
            if _TABLE_HEADER_RE.match(lines[index].rstrip("\r\n")) is not None:
                break

            if _entry_line_key(lines[index]) == entry_key:
                return "".join([
                    *lines[:index],
                    *lines[index + 1:],
                ]), True

    for index, line in enumerate(lines):
        if _entry_subtable_key(line) != entry_key:
            continue

        remove_end_index = len(lines)
        for next_index in range(index + 1, len(lines)):
            if _TABLE_HEADER_RE.match(lines[next_index].rstrip("\r\n")) is not None:
                remove_end_index = next_index
                break

        return "".join([
            *lines[:index],
            *lines[remove_end_index:],
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


def _entry_subtable_key(line: str):
    header_match = _TABLE_HEADER_RE.match(line.rstrip("\r\n"))
    if header_match is None:
        return None

    header_name = header_match.group(1).strip()
    if not header_name.startswith("entries."):
        return None

    raw_entry_key = header_name.removeprefix("entries.").strip()
    if raw_entry_key == "":
        return None

    if not raw_entry_key.startswith(("\"", "'")):
        if "." in raw_entry_key:
            return None

        return raw_entry_key

    try:
        parsed_key = toml.loads(f"key = {raw_entry_key}")
    except toml.TomlDecodeError:
        return None

    key = parsed_key.get("key")
    if not isinstance(key, str):
        return None

    return key
