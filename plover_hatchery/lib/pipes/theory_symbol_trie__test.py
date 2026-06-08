from plover.steno import Stroke
from plover_hatchery_lib_rs import TheorySymbol, TriePath
from plover_hatchery.lib.pipes.Plugin import define_plugin
from plover_hatchery.lib.pipes.compile_theory import compile_theory
from plover_hatchery.lib.pipes.floating_keys import floating_keys
from plover_hatchery.lib.pipes.theory_symbol_trie import ChordToTheorySymbolSearchResult, TheorySymbolsToTranslationSearchPath, theory_symbol_trie


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


def _build_lookup(entry_lines: dict[str, str], chords: dict[str, str]):
    def plugins():
        yield floating_keys("*")
        yield theory_symbol_trie(
            map_to_theory_symbols=_map_to_theory_symbols,
            theory_symbols_to_chords_dicts=[chords],
        )
        yield _choose_first_translation()

    return compile_theory(plugins).build_lookup(entry_lines.items())


def test__theory_symbol_trie__lookup_matches_entry_across_multiple_chords():
    lookup = _build_lookup(
        {"cat": "c.k a.a t.t"},
        {"k": "K", "a": "A", "t": "-T"},
    )

    assert lookup.lookup(("KAT",)) == "cat"


def test__theory_symbol_trie__chord_search_does_not_bleed_across_strokes():
    lookup = _build_lookup(
        {"act": "act.kt"},
        {"kt": "K-T"},
    )

    assert lookup.lookup(("K-T",)) == "act"
    assert lookup.lookup(("K", "T")) is None


def test__chord_to_theory_symbol_search_result__stores_theory_symbols_and_stroke():
    result = ChordToTheorySymbolSearchResult((TheorySymbol("k"), TheorySymbol("a")), Stroke.from_steno("KA"))

    assert tuple(theory_symbol.value for theory_symbol in result.theory_symbols) == ("k", "a")
    assert result.chord == Stroke.from_steno("KA")
    assert result == ChordToTheorySymbolSearchResult((TheorySymbol("k"), TheorySymbol("a")), Stroke.from_steno("KA"))


def test__theory_symbols_to_translation_search_path__defaults_and_custom_values():
    default_path = TheorySymbolsToTranslationSearchPath()

    assert default_path.trie_path.dst_node_id == TriePath.root().dst_node_id
    assert default_path.theory_symbols_and_chords_used == ()

    trie_path = TriePath(7, ())
    path = TheorySymbolsToTranslationSearchPath(trie_path, ("association",))

    assert path.trie_path.dst_node_id == 7
    assert path.theory_symbols_and_chords_used == ("association",)
