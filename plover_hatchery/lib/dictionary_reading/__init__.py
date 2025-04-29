from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Generator, TextIO, cast, final, TypedDict

import toml

from plover_hatchery.lib.trie import NondeterministicTrie


_HatcheryDictionaryMeta = TypedDict("_HatcheryDictionaryMeta", {
    "hatchery-dictionary-version": str,
})


@final
class HatcheryDictionary(TypedDict):
    meta: _HatcheryDictionaryMeta
    morphemes: dict[str, str]
    entries: dict[str, str]


@final
class _HatcheryDictionaryReader:
    def load(self, file: TextIO):
        return cast(HatcheryDictionary, cast(object, toml.load(file)))


    def read(self, dictionary_contents: HatcheryDictionary):
        assert dictionary_contents["meta"]["hatchery-dictionary-version"] == "0.0.0"

        return dictionary_contents



def read_hatchery_dictionary(filepath: str):
    reader = _HatcheryDictionaryReader()

    with open(filepath, "r", encoding="utf-8") as file:
        dictionary_contents = reader.load(file)

    return reader.read(dictionary_contents)

def all_entries(dictionary: HatcheryDictionary) -> Generator[tuple[str, str], None, None]:
    yield from dictionary["morphemes"].items()
    yield from dictionary["entries"].items()

