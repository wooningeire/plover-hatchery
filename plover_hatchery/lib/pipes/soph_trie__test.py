from plover.steno import Stroke
from plover_hatchery_lib_rs import Soph, TriePath
from plover_hatchery.lib.pipes.Plugin import define_plugin
from plover_hatchery.lib.pipes.compile_theory import compile_theory
from plover_hatchery.lib.pipes.floating_keys import floating_keys
from plover_hatchery.lib.pipes.soph_trie import ChordToSophSearchResult, SophsToTranslationSearchPath, soph_trie


def _map_to_sophs(cursor):
    try:
        return {cursor.tip().keysymbol().value}
    except TypeError:
        return set()


def _choose_first_translation():
    @define_plugin(_choose_first_translation)
    def plugin(get_plugin_api, **_):
        soph_trie_api = get_plugin_api(soph_trie)

        @soph_trie_api.select_translation.listen(_choose_first_translation)
        def _(choices, translations, **__):
            return translations[choices[0].lookup_result.translation_id]

    return plugin


def _build_lookup(entry_lines: dict[str, str], chords: dict[str, str]):
    def plugins():
        yield floating_keys("*")
        yield soph_trie(
            map_to_sophs=_map_to_sophs,
            sophs_to_chords_dicts=[chords],
        )
        yield _choose_first_translation()

    return compile_theory(plugins).build_lookup(entry_lines.items())


def test__soph_trie__lookup_matches_entry_across_multiple_chords():
    lookup = _build_lookup(
        {"cat": "c.k a.a t.t"},
        {"k": "K", "a": "A", "t": "-T"},
    )

    assert lookup.lookup(("KAT",)) == "cat"


def test__soph_trie__chord_search_does_not_bleed_across_strokes():
    lookup = _build_lookup(
        {"act": "act.kt"},
        {"kt": "K-T"},
    )

    assert lookup.lookup(("K-T",)) == "act"
    assert lookup.lookup(("K", "T")) is None


def test__chord_to_soph_search_result__stores_sophs_and_stroke():
    result = ChordToSophSearchResult((Soph("k"), Soph("a")), Stroke.from_steno("KA"))

    assert tuple(soph.value for soph in result.sophs) == ("k", "a")
    assert result.chord == Stroke.from_steno("KA")
    assert result == ChordToSophSearchResult((Soph("k"), Soph("a")), Stroke.from_steno("KA"))


def test__sophs_to_translation_search_path__defaults_and_custom_values():
    default_path = SophsToTranslationSearchPath()

    assert default_path.trie_path.dst_node_id == TriePath.root().dst_node_id
    assert default_path.sophs_and_chords_used == ()

    trie_path = TriePath(7, ())
    path = SophsToTranslationSearchPath(trie_path, ("association",))

    assert path.trie_path.dst_node_id == 7
    assert path.sophs_and_chords_used == ("association",)
