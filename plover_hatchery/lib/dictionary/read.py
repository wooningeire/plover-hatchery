from dataclasses import dataclass
from typing import Any, Generator, TextIO, cast, final

import toml

from .HatcheryDictionaryContents import HatcheryDictionaryContents


SUPPORTED_HATCHERY_FORMAT_VERSIONS = {"0.0.0", "0.1.0"}
ENTRY_FORMAT_SOPHEMES = "sophemes"
ENTRY_FORMAT_THEORY_SYMBOLS = "theory-symbols"
ENTRY_FORMATS_WITH_SEQUENCE = {
    ENTRY_FORMAT_SOPHEMES,
    ENTRY_FORMAT_THEORY_SYMBOLS,
}


class HatcheryDictionaryFormatError(ValueError):
    pass


@dataclass(frozen=True)
class HatcheryEntry:
    key: str
    format: str
    definition: str
    translation: str | None = None


@final
class _HatcheryDictionaryReader:
    def load(self, file: TextIO):
        return cast(HatcheryDictionaryContents, cast(object, toml.load(file)))


    def read(self, dictionary_contents: HatcheryDictionaryContents):
        assert (
            dictionary_contents["meta"]["hatchery-format-version"]
            in SUPPORTED_HATCHERY_FORMAT_VERSIONS
        )
        _ = tuple(entry_items(dictionary_contents))

        return dictionary_contents



def read_hatchery_dictionary(filepath: str):
    reader = _HatcheryDictionaryReader()

    with open(filepath, "r", encoding="utf-8") as file:
        dictionary_contents = reader.load(file)

    return reader.read(dictionary_contents)


def entry_items(dictionary: HatcheryDictionaryContents) -> Generator[HatcheryEntry, None, None]:
    entries = _entry_section(dictionary)
    for key, raw_entry in entries.items():
        yield normalize_entry(key, raw_entry)


def _entry_section(dictionary: HatcheryDictionaryContents) -> dict[str, Any]:
    entries = dict(dictionary).get("entries", {})
    if not isinstance(entries, dict):
        raise HatcheryDictionaryFormatError("[entries] must be a table")

    return entries


def normalize_entry(key: str, raw_entry: Any) -> HatcheryEntry:
    if isinstance(raw_entry, str):
        return HatcheryEntry(
            key=key,
            format=ENTRY_FORMAT_SOPHEMES,
            definition=raw_entry.strip(),
        )

    if not isinstance(raw_entry, dict):
        raise HatcheryDictionaryFormatError(
            f'Entry "{key}" must be a string or an entry object'
        )

    raw_format = raw_entry.get("format")
    if (
        not isinstance(raw_format, str)
        or raw_format not in ENTRY_FORMATS_WITH_SEQUENCE
    ):
        raise HatcheryDictionaryFormatError(
            f'Entry "{key}" has unsupported format "{raw_format}"'
        )

    definition_field = (
        "theory-symbols"
        if raw_format == ENTRY_FORMAT_THEORY_SYMBOLS
        else "sequence"
    )
    raw_sequence = raw_entry.get(definition_field)
    if not isinstance(raw_sequence, str):
        raise HatcheryDictionaryFormatError(
            f'Entry "{key}" with format "{raw_format}" must have a string {definition_field}'
        )

    raw_translation = raw_entry.get("translation")
    if raw_translation is not None and not isinstance(raw_translation, str):
        raise HatcheryDictionaryFormatError(
            f'Entry "{key}" translation must be a string'
        )

    return HatcheryEntry(
        key=key,
        format=raw_format,
        definition=raw_sequence.strip(),
        translation=raw_translation,
    )


def all_entries(dictionary: HatcheryDictionaryContents) -> Generator[tuple[str, str], None, None]:
    yield from dictionary["morphemes"].items()
    for entry in entry_items(dictionary):
        yield entry.key, entry.definition
