def test__build_lookup_hatchery__single_syllable():
    from .build_trie_from_dict import get_lookup_builder_hatchery
    from ..theory_defaults.lapwing import theory

    build_lookup_hatchery = get_lookup_builder_hatchery(theory)

    lookup, reverse_lookup = build_lookup_hatchery((
        "c.k r.r e.e!1 s.s t.t",
    ))

    assert lookup(("KREFT",)) == "crest"


def test__build_lookup_hatchery__prefix_string():
    from .build_trie_from_dict import get_lookup_builder_hatchery
    from ..theory_defaults.lapwing import theory

    build_lookup_hatchery = get_lookup_builder_hatchery(theory)

    lookup, reverse_lookup = build_lookup_hatchery((
        "c.k r.r i.i!1 s.s t.t ai.ee!2 l.l",
        "c.k r.r i.i!1 s.s t.t",
        "c.k r.r i.i!1",
    ))

    assert lookup(("KREUFT",)) == "crist"
    assert lookup(("KREUS", "TAEUL")) == "cristail"
    assert lookup(("KREU",)) == "cri"


def test__build_lookup_hatchery__reverse_lookup():
    from .build_trie_from_dict import get_lookup_builder_hatchery
    from ..theory_defaults.lapwing import theory

    build_lookup_hatchery = get_lookup_builder_hatchery(theory)

    lookup, reverse_lookup = build_lookup_hatchery((
        "c.k r.r i.i!1 s.s t.t ai.ee!2 l.l",
    ))

    outlines = reverse_lookup("cristail")

    assert all(
        outline in outlines
        for outline in (
            ("KREU", "STAEUL"),
            ("KREUS", "TAEUL"),
            ("KREUFT", "KWRAEUL"),
        )
    )
    