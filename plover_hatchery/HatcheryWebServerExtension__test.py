import json
from pathlib import Path
from typing import Any

import pytest

from plover_hatchery.HatcheryWebServerExtension import HatcheryWebServerExtension, is_allowed_origin
from plover_hatchery.Store import store
from plover_hatchery.lib.dictionary.write_entries import safe_entry_key_stem, unique_entry_key


class FakeHatcheryDictionary:
    def __init__(self):
        self.compile_calls = 0
        self.invalidate_calls = 0
        self.refresh_cache_calls: list[bool] = []

    def invalidate_lookup_cache(self) -> None:
        self.invalidate_calls += 1

    def compile(self, *, refresh_cache: bool=False) -> dict[str, Any]:
        self.compile_calls += 1
        self.refresh_cache_calls.append(refresh_cache)
        store.translations = ["cat"]
        store.breakdown_translation = lambda translation: json.dumps([
            {"entry": translation}
        ])
        store.breakdown_lookup = lambda outline, translations: json.dumps([
            {"outline": outline, "translations": translations}
        ])
        return {"status": "compiled"}


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


def _client():
    extension = HatcheryWebServerExtension(object())
    app = extension._HatcheryWebServerExtension__app
    return app.test_client()


def _sample_dictionary_text(*, include_entries: bool=True):
    entries_section = """
[entries]
cat = "{@k} a.a t.t"
""".rstrip() if include_entries else ""

    return f"""
[meta]
hatchery-format-version = "0.0.0"

[morphemes]
"@k" = "c.k"
{entries_section}

[other]
value = "untouched"
""".strip()


def test__status_route__identifies_hatchery_api():
    response = _client().get("/api/status")

    assert response.status_code == 200
    assert response.get_json() == {
        "service": "plover-hatchery",
        "ok": True,
    }


def test__compile_route__compiles_registered_hatchery_dictionaries():
    dictionary = FakeHatcheryDictionary()
    store.register_hatchery_dictionary("fake.hatchery", dictionary)

    response = _client().post("/api/compile")

    assert response.status_code == 200
    assert dictionary.compile_calls == 1
    assert dictionary.refresh_cache_calls == [False]
    assert response.get_json() == {
        "dictionaries": [{"status": "compiled"}],
    }


def test__compile_route__refreshes_cache_when_requested():
    dictionary = FakeHatcheryDictionary()
    store.register_hatchery_dictionary("fake.hatchery", dictionary)

    response = _client().post("/api/compile", json={"refreshCache": True})

    assert response.status_code == 200
    assert dictionary.compile_calls == 1
    assert dictionary.refresh_cache_calls == [True]
    assert response.get_json() == {
        "dictionaries": [{"status": "compiled"}],
    }


@pytest.mark.parametrize("origin", [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:65535",
    "https://localhost:443",
    "http://127.0.0.1",
    "http://127.0.0.1:5177",
    "http://[::1]",
    "http://[::1]:5178",
    "https://vaie.art",
])
def test__is_allowed_origin__allows_localhost_and_hatchery(origin: str):
    assert is_allowed_origin(origin)


@pytest.mark.parametrize("origin", [
    "ftp://localhost:5173",
    "http://localhost:not-a-port",
    "http://localhost:65536",
    "http://localhost:5173/path",
    "http://localhost.evil.test:5173",
    "http://vaie.art",
    "https://evil.vaie.art",
])
def test__is_allowed_origin__rejects_other_origins(origin: str):
    assert not is_allowed_origin(origin)


@pytest.mark.parametrize("origin", [
    "http://localhost:5173",
    "http://127.0.0.1:5177",
    "https://vaie.art",
])
def test__web_server__allows_web_ui_origins(origin: str):
    response = _client().post("/api/compile", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "*"


def test__web_server__allows_json_compile_preflight_from_web_ui_origin():
    response = _client().options(
        "/api/compile",
        headers={
            "Origin": "http://localhost:9999",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "*"
    assert response.headers["Access-Control-Allow-Headers"] == "Content-Type"


def test__breakdown_translation_route__compiles_before_serving_breakdown():
    dictionary = FakeHatcheryDictionary()
    store.register_hatchery_dictionary("fake.hatchery", dictionary)

    response = _client().get("/api/breakdown_translation/cat")

    assert response.status_code == 200
    assert dictionary.compile_calls == 1
    assert dictionary.refresh_cache_calls == [False]
    assert json.loads(response.get_data(as_text=True)) == [{"entry": "cat"}]


def test__dictionaries_route__lists_registered_hatchery_dictionaries(tmp_path: Path):
    dictionary_path = tmp_path / "user-added.hatchery"
    store.register_hatchery_dictionary(str(dictionary_path), FakeHatcheryDictionary())

    response = _client().get("/api/dictionaries")

    assert response.status_code == 200
    assert response.get_json() == {
        "dictionaries": [
            {
                "path": str(dictionary_path),
                "label": "user-added.hatchery",
            },
        ],
    }


def test__add_entry_route__appends_entry_and_compiles_changed_dictionary(tmp_path: Path):
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text(_sample_dictionary_text(), encoding="utf-8")
    dictionary = FakeHatcheryDictionary()
    store.register_hatchery_dictionary(str(dictionary_path), dictionary)

    response = _client().post("/api/entries", json={
        "dictionaryPath": str(dictionary_path),
        "translation": "cat",
        "definition": "{@k} a.a t.t",
    })

    assert response.status_code == 200
    assert response.get_json() == {
        "entry": {
            "key": "cat:2",
            "translation": "cat",
            "definition": "{@k} a.a t.t",
        },
        "compile": {
            "path": str(dictionary_path),
            "status": "compiled",
        },
    }
    assert dictionary.invalidate_calls == 1
    assert dictionary.compile_calls == 1
    assert dictionary.refresh_cache_calls == [False]

    new_dictionary_text = dictionary_path.read_text(encoding="utf-8")
    assert '"cat:2" = "{@k} a.a t.t"' in new_dictionary_text
    assert new_dictionary_text.index('"cat:2" = "{@k} a.a t.t"') < new_dictionary_text.index("[other]")
    assert 'value = "untouched"' in new_dictionary_text


def test__add_entry_route__appends_entries_section_when_missing(tmp_path: Path):
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text(_sample_dictionary_text(include_entries=False), encoding="utf-8")
    dictionary = FakeHatcheryDictionary()
    store.register_hatchery_dictionary(str(dictionary_path), dictionary)

    response = _client().post("/api/entries", json={
        "dictionaryPath": str(dictionary_path),
        "translation": "cat",
        "definition": "{@k} a.a t.t",
    })

    assert response.status_code == 200
    assert "\n[entries]\n\"cat\" = \"{@k} a.a t.t\"\n" in dictionary_path.read_text(encoding="utf-8")


def test__add_entry_route__rejects_unknown_dictionary(tmp_path: Path):
    response = _client().post("/api/entries", json={
        "dictionaryPath": str(tmp_path / "missing.hatchery"),
        "translation": "cat",
        "definition": "c.k a.a t.t",
    })

    assert response.status_code == 404
    assert response.get_json() == {
        "error": "Hatchery dictionary is not loaded",
    }


def test__add_entry_route__rejects_invalid_definition(tmp_path: Path):
    dictionary_path = tmp_path / "sample.hatchery"
    original_text = _sample_dictionary_text()
    dictionary_path.write_text(original_text, encoding="utf-8")
    store.register_hatchery_dictionary(str(dictionary_path), FakeHatcheryDictionary())

    response = _client().post("/api/entries", json={
        "dictionaryPath": str(dictionary_path),
        "translation": "cat",
        "definition": "not-a-definition",
    })

    assert response.status_code == 400
    assert "Definition could not be parsed" in response.get_json()["error"]
    assert dictionary_path.read_text(encoding="utf-8") == original_text


def test__add_entry_route__rejects_missing_transclusion(tmp_path: Path):
    dictionary_path = tmp_path / "sample.hatchery"
    original_text = _sample_dictionary_text()
    dictionary_path.write_text(original_text, encoding="utf-8")
    store.register_hatchery_dictionary(str(dictionary_path), FakeHatcheryDictionary())

    response = _client().post("/api/entries", json={
        "dictionaryPath": str(dictionary_path),
        "translation": "cat",
        "definition": "{missing}",
    })

    assert response.status_code == 400
    assert "Definition could not be resolved" in response.get_json()["error"]
    assert dictionary_path.read_text(encoding="utf-8") == original_text


def test__add_entry_route__rejects_translation_mismatch(tmp_path: Path):
    dictionary_path = tmp_path / "sample.hatchery"
    original_text = _sample_dictionary_text()
    dictionary_path.write_text(original_text, encoding="utf-8")
    store.register_hatchery_dictionary(str(dictionary_path), FakeHatcheryDictionary())

    response = _client().post("/api/entries", json={
        "dictionaryPath": str(dictionary_path),
        "translation": "dog",
        "definition": "{@k} a.a t.t",
    })

    assert response.status_code == 400
    assert 'Definition resolves to "cat", not "dog"' in response.get_json()["error"]
    assert dictionary_path.read_text(encoding="utf-8") == original_text


def test__unique_entry_key__uses_safe_stem_and_numeric_suffixes():
    assert safe_entry_key_stem("Can't stop!") == "can't-stop"
    assert safe_entry_key_stem("@#^") == "entry"
    assert unique_entry_key("cat", {"cat", "cat:2"}) == "cat:3"
