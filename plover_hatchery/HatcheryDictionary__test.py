from pathlib import Path

import pytest

from plover_hatchery.HatcheryDictionary import HatcheryDictionary
from plover_hatchery.Store import store


@pytest.fixture(autouse=True)
def _reset_store():
    old_dictionaries = dict(store.hatchery_dictionaries)
    old_breakdown_translation = store.breakdown_translation
    old_breakdown_lookup = store.breakdown_lookup
    old_translations = store.translations
    old_trie = store.trie

    store.hatchery_dictionaries.clear()
    store.breakdown_translation = None
    store.breakdown_lookup = None
    store.translations = None
    store.trie = None

    yield

    store.hatchery_dictionaries.clear()
    store.hatchery_dictionaries.update(old_dictionaries)
    store.breakdown_translation = old_breakdown_translation
    store.breakdown_lookup = old_breakdown_lookup
    store.translations = old_translations
    store.trie = old_trie


def test__hatchery_dictionary__load_registers_and_primes_lookup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    dictionary = HatcheryDictionary()
    dictionary_path = tmp_path / "not-read-during-load.hatchery"
    compile_calls = 0

    def compile_lookup():
        nonlocal compile_calls
        compile_calls += 1
        dictionary._HatcheryDictionary__maybe_lookup = lambda stroke_stenos: (
            "cat" if stroke_stenos == ("KAT",) else None
        )
        dictionary._HatcheryDictionary__maybe_reverse_lookup = lambda translation: (
            [("KAT",)] if translation == "cat" else []
        )
        return {"status": "compiled"}

    monkeypatch.setattr(dictionary, "compile", compile_lookup)

    dictionary._load(str(dictionary_path))

    assert store.hatchery_dictionaries == {
        str(dictionary_path): dictionary,
    }
    assert compile_calls == 1

    assert dictionary.get(("KAT",), "fallback") == "cat"
    assert compile_calls == 1
    assert dictionary[("KAT",)] == "cat"
    assert compile_calls == 1
    assert dictionary.get(("TKOG",), "fallback") == "fallback"
    with pytest.raises(KeyError):
        dictionary[("TKOG",)]


def test__hatchery_dictionary__reverse_lookup_uses_lookup_primed_during_load(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    dictionary = HatcheryDictionary()
    dictionary_path = tmp_path / "not-read-during-load.hatchery"
    compile_calls = 0

    def compile_lookup():
        nonlocal compile_calls
        compile_calls += 1
        dictionary._HatcheryDictionary__maybe_lookup = lambda _: None
        dictionary._HatcheryDictionary__maybe_reverse_lookup = lambda translation: (
            [("KAT",)] if translation == "cat" else []
        )
        return {"status": "compiled"}

    monkeypatch.setattr(dictionary, "compile", compile_lookup)

    dictionary._load(str(dictionary_path))

    assert compile_calls == 1
    assert dictionary.reverse_lookup("cat") == [("KAT",)]
    assert compile_calls == 1
    assert dictionary.reverse_lookup("dog") == []
    assert compile_calls == 1
