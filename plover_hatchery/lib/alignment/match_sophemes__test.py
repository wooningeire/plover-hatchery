def test__match_sophemes__baseline():
    from plover_hatchery.lib.alignment.match_sophemes import match_keysymbols_to_chars
    from plover_hatchery.lib.sopheme import Keysymbol

    assert (
        " ".join(str(sopheme) for sopheme in match_keysymbols_to_chars(Keysymbol.parse_seq(transcription=" { ~ a . k w ii . * e s } "), "acquiesce"))
        == "a.a!2 cq.k u.w i.ii e.e!1 sc.s e."
    )

    assert (
        " ".join(str(sopheme) for sopheme in match_keysymbols_to_chars(Keysymbol.parse_seq(" { z * ae . g ou t } "), "zygote"))
        == "z.z y.ae!1 g.g o.ou t.t e."
    )

def test__match_sophemes__keysymbol_cluster_with_gap():
    from plover_hatchery.lib.alignment.match_sophemes import match_keysymbols_to_chars
    from plover_hatchery.lib.sopheme import Keysymbol

    assert (
        " ".join(str(sopheme) for sopheme in match_keysymbols_to_chars(Keysymbol.parse_seq(" { ee sh n } "), "ation"))
        == "a.ee ti.sh o. n.n"
    )

