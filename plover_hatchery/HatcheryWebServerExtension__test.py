import json
from typing import Any

import pytest

from plover_hatchery.HatcheryWebServerExtension import HatcheryWebServerExtension
from plover_hatchery.Store import store


class FakeHatcheryDictionary:
    def __init__(self):
        self.compile_calls = 0
        self.refresh_cache_calls: list[bool] = []

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
    "http://localhost:5173",
    "http://127.0.0.1:5177",
])
def test__web_server__allows_local_web_ui_origins(origin: str):
    response = _client().post("/api/compile", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "*"


def test__breakdown_translation_route__compiles_before_serving_breakdown():
    dictionary = FakeHatcheryDictionary()
    store.register_hatchery_dictionary("fake.hatchery", dictionary)

    response = _client().get("/api/breakdown_translation/cat")

    assert response.status_code == 200
    assert dictionary.compile_calls == 1
    assert dictionary.refresh_cache_calls == [False]
    assert json.loads(response.get_data(as_text=True)) == [{"entry": "cat"}]
