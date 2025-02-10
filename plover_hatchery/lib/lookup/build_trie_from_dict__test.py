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


def test__build_lookup_hatchery__sample__investigate():
    from .build_trie_from_dict import get_lookup_builder_hatchery
    from ..theory_defaults.lapwing import theory

    build_lookup_hatchery = get_lookup_builder_hatchery(theory)

    lookup, reverse_lookup = build_lookup_hatchery((
        "i.i n.n v.v e.e!1 s.s t.t i.I2 g.g a.ee t.t e.",
    ))

    outlines = reverse_lookup("investigate")

    assert lookup(("EUPB", "SREFT", "TKPWAEUT")) == "investigate"
    assert lookup(("EUPB", "SREFT")) is None

    assert ("EUPB", "SREFT", "TKPWAEUT") in outlines
    assert ("EUPB", "SREFT") not in outlines


def test__build_lookup_hatchery__sample__information():
    from .build_trie_from_dict import get_lookup_builder_hatchery
    from ..theory_defaults.lapwing import theory

    build_lookup_hatchery = get_lookup_builder_hatchery(theory)

    lookup, reverse_lookup = build_lookup_hatchery((
        "i.i!2 n.n f.f o.@r r.r m.m a.ee!1 ti.sh o. n.n",
    ))

    outlines = reverse_lookup("information")

    print(outlines)

    assert lookup(("TPWORPLGS",)) == "information"

    assert ("TPWORPLGS",) in outlines

   