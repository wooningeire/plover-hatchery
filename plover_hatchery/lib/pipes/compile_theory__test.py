import json
import pickle
from pathlib import Path

from plover_hatchery_lib_rs import NondeterministicTrie as RsNondeterministicTrie
from plover_hatchery_lib_rs import TransitionFlagManager

from plover_hatchery.lib.pipes.Plugin import define_plugin
from plover_hatchery.lib.pipes.compile_theory import compile_theory
from plover_hatchery.lib.pipes.floating_keys import floating_keys
from plover_hatchery.lib.pipes.theory_symbol_trie import theory_symbol_trie


THEORY_SYMBOL_TRIE_CACHE_KEY = "theory_symbol_trie"
LEGACY_THEORY_SYMBOL_TRIE_CACHE_KEY = "soph_trie"


def _map_to_theory_symbols(cursor):
    try:
        return {cursor.tip().keysymbol().value}
    except TypeError:
        return set()


def _choose_first_translation():
    @define_plugin(_choose_first_translation)
    def plugin(get_plugin_api, **_):
        theory_symbol_trie_api = get_plugin_api(theory_symbol_trie)

        @theory_symbol_trie_api.select_translation.listen(_choose_first_translation)
        def _(choices, translations, **__):
            return translations[choices[0].lookup_result.translation_id]

    return plugin


def _test_theory():
    def plugins():
        yield floating_keys("*")
        yield theory_symbol_trie(
            map_to_theory_symbols=_map_to_theory_symbols,
            theory_symbols_to_chords_dicts=[{"k": "K", "a": "A", "kt": "K-T", "t": "-T"}],
        )
        yield _choose_first_translation()

    return compile_theory(plugins)


def _build_lookup(filename: Path, entry_lines=None, *, refresh_cache=False):
    if entry_lines is None:
        entry_lines = {"cat": "c.k a.a t.t"}.items()

    return _test_theory().build_lookup(
        entry_lines=entry_lines,
        filename=str(filename),
        refresh_cache=refresh_cache,
    )


def _cache_path(dictionary_path: Path):
    return dictionary_path.with_suffix(".hatchery.compiled-trie.pickle")


def _entry_lines_should_not_be_loaded():
    raise AssertionError("entry lines should not be loaded when the compiled trie cache is valid")


def _read_cache_payload(dictionary_path: Path):
    with _cache_path(dictionary_path).open("rb") as file:
        return pickle.load(file)


def _write_cache_payload(dictionary_path: Path, payload):
    with _cache_path(dictionary_path).open("wb") as file:
        pickle.dump(payload, file, protocol=pickle.HIGHEST_PROTOCOL)


def _rewrite_theory_symbol_trie_cache_to_legacy_payload_format(dictionary_path: Path):
    payload = _read_cache_payload(dictionary_path)
    theory_symbol_trie_cache = payload["plugins"][THEORY_SYMBOL_TRIE_CACHE_KEY]

    theory_symbol_trie_cache["trie"] = RsNondeterministicTrie.from_state_bytes(
        theory_symbol_trie_cache.pop("trie_bytes")
    ).export_state()
    theory_symbol_trie_cache["transition_flags"] = TransitionFlagManager.from_state_bytes(
        theory_symbol_trie_cache.pop("transition_flags_bytes")
    ).export_state()
    payload.pop("payload_format", None)

    _write_cache_payload(dictionary_path, payload)


def _rewrite_theory_symbol_trie_cache_to_legacy_plugin_key(dictionary_path: Path):
    payload = _read_cache_payload(dictionary_path)
    payload["plugins"][LEGACY_THEORY_SYMBOL_TRIE_CACHE_KEY] = payload["plugins"].pop(
        THEORY_SYMBOL_TRIE_CACHE_KEY
    )
    _write_cache_payload(dictionary_path, payload)


def test__compile_theory__loads_compiled_trie_cache(tmp_path: Path, capsys):
    dictionary_path = tmp_path / "sample.hatchery"

    first_lookup = _build_lookup(dictionary_path)
    assert first_lookup.lookup(("KAT",)) == "cat"

    cache_path = _cache_path(dictionary_path)
    assert cache_path.exists()

    _ = capsys.readouterr()
    second_lookup = _build_lookup(dictionary_path)
    output = capsys.readouterr().out

    assert "Loaded compiled trie cache" in output
    assert second_lookup.lookup(("KAT",)) == "cat"


def test__compile_theory__breakdown_translation_uses_entry_id_space_after_rebuild(tmp_path: Path):
    dictionary_path = tmp_path / "sample.hatchery"
    theory = _test_theory()
    entry_lines = {"cat": "c.k a.a t.t"}.items()

    first_lookup = theory.build_lookup(
        entry_lines=entry_lines,
        filename=str(dictionary_path),
    )
    assert first_lookup.lookup(("KAT",)) == "cat"
    assert json.loads(first_lookup.breakdown_translation("cat"))[0]["entry"] == "cat = c.k a.a t.t"

    second_lookup = theory.build_lookup(
        entry_lines={"act": "act.kt"}.items(),
        filename=str(dictionary_path),
        refresh_cache=True,
    )

    assert second_lookup.lookup(("KAT",)) is None
    assert second_lookup.lookup(("K-T",)) == "act"
    assert [
        item["entry"]
        for item in json.loads(second_lookup.breakdown_translation("act"))
    ] == ["act = act.kt"]


def test__compile_theory__keeps_lookup_state_independent_after_later_build():
    theory = _test_theory()

    first_lookup = theory.build_lookup(
        entry_lines={"cat": "c.k a.a t.t"}.items(),
        filename="",
    )
    assert first_lookup.lookup(("KAT",)) == "cat"

    second_lookup = theory.build_lookup(
        entry_lines={"act": "act.kt"}.items(),
        filename="",
    )

    assert second_lookup.lookup(("K-T",)) == "act"
    assert first_lookup.lookup(("KAT",)) == "cat"
    assert first_lookup.lookup(("K-T",)) is None


def test__compile_theory__saves_compiled_trie_cache_as_rust_bytes(tmp_path: Path):
    dictionary_path = tmp_path / "sample.hatchery"

    first_lookup = _build_lookup(dictionary_path)
    assert first_lookup.lookup(("KAT",)) == "cat"

    payload = _read_cache_payload(dictionary_path)
    theory_symbol_trie_cache = payload["plugins"][THEORY_SYMBOL_TRIE_CACHE_KEY]

    assert payload["payload_format"] == 2
    assert isinstance(theory_symbol_trie_cache["trie_bytes"], bytes)
    assert isinstance(theory_symbol_trie_cache["transition_flags_bytes"], bytes)
    assert "trie" not in theory_symbol_trie_cache
    assert "transition_flags" not in theory_symbol_trie_cache


def test__compile_theory__loads_file_fingerprint_cache_before_loading_entries(tmp_path: Path, capsys):
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text("source version 1", encoding="utf-8")

    first_lookup = _build_lookup(dictionary_path)
    assert first_lookup.lookup(("KAT",)) == "cat"
    assert _cache_path(dictionary_path).exists()

    _ = capsys.readouterr()
    second_lookup = _build_lookup(dictionary_path, _entry_lines_should_not_be_loaded)
    output = capsys.readouterr().out

    assert "Loaded compiled trie cache" in output
    assert "Parsed" not in output
    assert second_lookup.lookup(("KAT",)) == "cat"


def test__compile_theory__does_not_use_file_fingerprint_cache_after_source_changes(tmp_path: Path):
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text("source version 1", encoding="utf-8")

    first_lookup = _build_lookup(dictionary_path)
    assert first_lookup.lookup(("KAT",)) == "cat"

    dictionary_path.write_text("source version 2", encoding="utf-8")

    try:
        _build_lookup(dictionary_path, _entry_lines_should_not_be_loaded)
    except AssertionError as e:
        assert str(e) == "entry lines should not be loaded when the compiled trie cache is valid"
    else:
        raise AssertionError("stale file-fingerprint cache loaded without reading entries")


def test__compile_theory__loads_legacy_cache_before_loading_entries_when_cache_is_newer(tmp_path: Path, capsys):
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text("source version 1", encoding="utf-8")

    first_lookup = _build_lookup(dictionary_path)
    assert first_lookup.lookup(("KAT",)) == "cat"

    payload = _read_cache_payload(dictionary_path)
    payload.pop("source_hash_kind", None)
    payload["source_hash"] = "legacy-entry-hash"
    _write_cache_payload(dictionary_path, payload)

    _ = capsys.readouterr()
    second_lookup = _build_lookup(dictionary_path, _entry_lines_should_not_be_loaded)
    output = capsys.readouterr().out

    assert "Loaded compiled trie cache" in output
    assert "Parsed" not in output
    assert second_lookup.lookup(("KAT",)) == "cat"


def test__compile_theory__loads_legacy_theory_symbol_trie_cache_key(tmp_path: Path, capsys):
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text("source version 1", encoding="utf-8")

    first_lookup = _build_lookup(dictionary_path)
    assert first_lookup.lookup(("KAT",)) == "cat"
    _rewrite_theory_symbol_trie_cache_to_legacy_plugin_key(dictionary_path)

    _ = capsys.readouterr()
    second_lookup = _build_lookup(dictionary_path, _entry_lines_should_not_be_loaded)
    output = capsys.readouterr().out

    assert "Loaded compiled trie cache" in output
    assert "Parsed" not in output
    assert second_lookup.lookup(("KAT",)) == "cat"


def test__compile_theory__does_not_refresh_legacy_payload_cache_during_default_load(tmp_path: Path, capsys):
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text("source version 1", encoding="utf-8")

    first_lookup = _build_lookup(dictionary_path)
    assert first_lookup.lookup(("KAT",)) == "cat"
    _rewrite_theory_symbol_trie_cache_to_legacy_payload_format(dictionary_path)

    _ = capsys.readouterr()
    second_lookup = _build_lookup(dictionary_path, _entry_lines_should_not_be_loaded)
    output = capsys.readouterr().out

    assert "Loaded compiled trie cache" in output
    assert "Refreshed compiled trie cache" not in output
    assert "Parsed" not in output
    assert second_lookup.lookup(("KAT",)) == "cat"

    payload = _read_cache_payload(dictionary_path)
    theory_symbol_trie_cache = payload["plugins"][THEORY_SYMBOL_TRIE_CACHE_KEY]
    assert "trie" in theory_symbol_trie_cache
    assert "transition_flags" in theory_symbol_trie_cache


def test__compile_theory__refreshes_legacy_payload_cache_when_requested(tmp_path: Path, capsys):
    dictionary_path = tmp_path / "sample.hatchery"
    dictionary_path.write_text("source version 1", encoding="utf-8")

    first_lookup = _build_lookup(dictionary_path)
    assert first_lookup.lookup(("KAT",)) == "cat"
    _rewrite_theory_symbol_trie_cache_to_legacy_payload_format(dictionary_path)

    _ = capsys.readouterr()
    second_lookup = _build_lookup(
        dictionary_path,
        _entry_lines_should_not_be_loaded,
        refresh_cache=True,
    )
    output = capsys.readouterr().out

    assert "Loaded compiled trie cache" in output
    assert "Refreshed compiled trie cache" in output
    assert "Parsed" not in output
    assert second_lookup.lookup(("KAT",)) == "cat"

    payload = _read_cache_payload(dictionary_path)
    theory_symbol_trie_cache = payload["plugins"][THEORY_SYMBOL_TRIE_CACHE_KEY]
    assert payload["payload_format"] == 2
    assert isinstance(theory_symbol_trie_cache["trie_bytes"], bytes)
    assert isinstance(theory_symbol_trie_cache["transition_flags_bytes"], bytes)
