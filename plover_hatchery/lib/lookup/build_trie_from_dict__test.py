def test__build_lookup_hatchery__single_syllable():
    from ..theory_presets.lapwing import theory


    lookup, reverse_lookup = theory.build_lookup(entries=(
        "c.k r.r e.e!1 s.s t.t",
    ))


    assert lookup(("KREFT",)) == "crest"


def test__build_lookup_hatchery__prefix_string():
    from ..theory_presets.lapwing import theory

    lookup, reverse_lookup = theory.build_lookup(entries=(
        "c.k r.r i.i!1 s.s t.t ai.ee!2 l.l",
        "c.k r.r i.i!1 s.s t.t",
        "c.k r.r i.i!1",
    ))


    assert lookup(("KREUFT",)) == "crist"
    assert lookup(("KREUS", "TAEUL")) == "cristail"
    assert lookup(("KREU",)) == "cri"


def test__build_lookup_hatchery__reverse_lookup():
    from ..theory_presets.lapwing import theory

    lookup, reverse_lookup = theory.build_lookup(entries=(
        "c.k r.r i.i!1 s.s t.t ai.ee!2 l.l",
    ))


    outlines = reverse_lookup("cristail")

    assert ("KREU", "STAEUL") in outlines
    assert ("KREUS", "TAEUL") in outlines
    assert ("KREUFT", "KWRAEUL") in outlines


def test__build_lookup_hatchery__boundary_elision():
    from ..theory_presets.lapwing import theory

    lookup, reverse_lookup = theory.build_lookup(entries=(
        "i.i n.n v.v e.e!1 s.s t.t i.I2 g.g a.ee t.t e.",
    ))


    assert lookup(("EUPB", "SREFT", "TKPWAEUT")) == "investigate"
    assert lookup(("EUPB", "SREFT")) is None

    outlines = reverse_lookup("investigate")
    assert ("EUPB", "SREFT", "TKPWAEUT") in outlines
    assert ("EUPB", "SREFT") not in outlines


def test__build_lookup_hatchery__cluster_elision():
    from ..theory_presets.lapwing import theory

    lookup, reverse_lookup = theory.build_lookup(entries=(
        "i.i!2 n.n f.f o.@r r.r m.m a.ee!1 ti.sh o. n.n",
    ))


    assert lookup(("TPWORPLGS",)) == "information"

    outlines = reverse_lookup("information")
    assert ("TPWORPLGS",) in outlines


def test__build_lookup_hatchery__optional_sounds():
    from ..theory_presets.lapwing import theory

    lookup, reverse_lookup = theory.build_lookup(entries=(
        "f.f i.i!1 g.g .y1? u.@r r.r e.",
    ))


    assert lookup(("TPEUG", "KWHUR")) == "figure"
    assert lookup(("TPEUG", "KWRUR")) == "figure"
    assert lookup(("TPEU", "TKPWUR")) == "figure"

    outlines = reverse_lookup("figure")
    assert ("TPEUG", "KWHUR") in outlines
    assert ("TPEUG", "KWRUR") in outlines
    assert ("TPEU", "TKPWUR") in outlines


def test__build_lookup_hatchery__cycling():
    from ..theory_presets.lapwing import theory

    lookup, reverse_lookup = theory.build_lookup(entries=(
        # "c.k o.ou a.a!1 g.g .y? u.UU l.l a.ee t.t e.",
        "t.t a.ee!1 p.p e. w.w o.@@r!3 r.r m.m",
        "i.i n.n f.f o.or!1 r.r m.m",
    ))


    assert lookup(("TPWORPL",)) == "inform"
    assert lookup(("TPWORPL", "#TPHEGT")) == "tapeworm"


def test__build_lookup_hatchery__ng():
    from ..theory_presets.lapwing import theory

    lookup, reverse_lookup = theory.build_lookup(entries=(
        "th.th i.i!1 n.ng k.k",
    ))


    assert lookup(("TH*EUPBG",)) == "think"
