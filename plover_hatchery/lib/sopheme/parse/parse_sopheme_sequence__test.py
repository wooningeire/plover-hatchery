from plover_hatchery.lib.sopheme.parse import parse_sopheme_sequence
from plover_hatchery.lib.sopheme.Sopheme import Sopheme, Keysymbol


def _attempt_recreate_sopheme_seq(sopheme_seq: str):
    assert sopheme_seq == Sopheme.format_seq(parse_sopheme_sequence(sopheme_seq))


def test__parse_sopheme_sequence__single_sopheme():
    _attempt_recreate_sopheme_seq("a.@!2?")

def test__parse_sopheme_sequence__multiple_sophemes():
    _attempt_recreate_sopheme_seq("h.h y.ae!1 d.d r.r o.@ g.jh e.E5 n.n")

def test__parse_sopheme_sequence__keysymbol_groups():
    _attempt_recreate_sopheme_seq("a.a n.ng x.(g z) i.ae!1 e.@ t.t y.iy")