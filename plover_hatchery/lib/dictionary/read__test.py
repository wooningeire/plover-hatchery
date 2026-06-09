from pathlib import Path

import pytest

from plover_hatchery.lib.dictionary.read import (
    HatcheryDictionaryFormatError,
    HatcheryEntry,
    all_entries,
    entry_items,
    read_hatchery_dictionary,
)


def test__read_hatchery_dictionary__loads_expected_sections(tmp_path: Path) -> None:
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text(
        """
[meta]
hatchery-format-version = "0.0.0"

[morphemes]
"@k" = "c.k"

[entries]
crest = "{@k} r.r e.e!1 s.s t.t"
""".strip(),
        encoding="utf-8",
    )

    dictionary = read_hatchery_dictionary(str(dictionary_path))

    assert dictionary["meta"]["hatchery-format-version"] == "0.0.0"
    assert dictionary["morphemes"] == {"@k": "c.k"}
    assert dictionary["entries"] == {"crest": "{@k} r.r e.e!1 s.s t.t"}


def test__read_hatchery_dictionary__accepts_sopheme_entry_objects(tmp_path: Path) -> None:
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text(
        """
[meta]
hatchery-format-version = "0.1.0"

[morphemes]

[entries."hang:1"]
format = "sophemes"
sequence = "h.[h] a.ae ng./ng/"
""".strip(),
        encoding="utf-8",
    )

    dictionary = read_hatchery_dictionary(str(dictionary_path))

    assert list(entry_items(dictionary)) == [
        HatcheryEntry(
            key="hang:1",
            format="sophemes",
            definition="h.[h] a.ae ng./ng/",
            translation=None,
        ),
    ]
    assert list(all_entries(dictionary)) == [
        ("hang:1", "h.[h] a.ae ng./ng/"),
    ]


def test__read_hatchery_dictionary__accepts_theory_symbol_entry_objects(tmp_path: Path) -> None:
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text(
        """
[meta]
hatchery-format-version = "0.1.0"

[morphemes]

[entries."hang:1"]
format = "theory-symbols"
theory-symbols = "H A NG"
translation = "hang"
""".strip(),
        encoding="utf-8",
    )

    dictionary = read_hatchery_dictionary(str(dictionary_path))

    entry = HatcheryEntry(
        key="hang:1",
        format="theory-symbols",
        definition="H A NG",
        translation="hang",
    )
    assert list(entry_items(dictionary)) == [entry]


def test__read_hatchery_dictionary__rejects_unsupported_entry_object_format(tmp_path: Path) -> None:
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text(
        """
[meta]
hatchery-format-version = "0.1.0"

[morphemes]

[entries.cat]
format = "sophs"
sophs = "K A T"
translation = "cat"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(HatcheryDictionaryFormatError):
        read_hatchery_dictionary(str(dictionary_path))


def test__read_hatchery_dictionary__rejects_unsupported_format_version(tmp_path: Path) -> None:
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text(
        """
[meta]
hatchery-format-version = "9.9.9"

[morphemes]

[entries]
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(AssertionError):
        read_hatchery_dictionary(str(dictionary_path))


def test__all_entries__yields_morphemes_before_entries() -> None:
    assert list(
        all_entries({
            "meta": {"hatchery-format-version": "0.0.0"},
            "morphemes": {"@k": "c.k", "@r": "r.r"},
            "entries": {"crest": "{@k} {@r} e.e!1 s.s t.t"},
        })
    ) == [
        ("@k", "c.k"),
        ("@r", "r.r"),
        ("crest", "{@k} {@r} e.e!1 s.s t.t"),
    ]
