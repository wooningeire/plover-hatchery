from typing import Generator, TextIO, cast, final

import toml

from .HatcheryDictionaryContents import HatcheryDictionaryContents


@final
class _HatcheryDictionaryReader:
    def load(self, file: TextIO):
        return cast(HatcheryDictionaryContents, cast(object, toml.load(file)))


    def read(self, dictionary_contents: HatcheryDictionaryContents):
        assert dictionary_contents["meta"]["hatchery-format-version"] == "0.0.0"

        return dictionary_contents



def read_hatchery_dictionary(filepath: str):
    reader = _HatcheryDictionaryReader()

    with open(filepath, "r", encoding="utf-8") as file:
        dictionary_contents = reader.load(file)

    return reader.read(dictionary_contents)

def all_entries(dictionary: HatcheryDictionaryContents) -> Generator[tuple[str, str], None, None]:
    yield from dictionary["morphemes"].items()
    yield from dictionary["entries"].items()

