from plover_hatchery.lib.sopheme.parse import parse_entry_definition
from plover_hatchery.lib.sopheme.Sopheme import Sopheme, Keysymbol


def _check_parsing_is_reversible(sopheme_seq: str):
    assert sopheme_seq == " ".join(str(entity) for entity in parse_entry_definition(sopheme_seq))


def test__parse_sopheme_sequence__single_sopheme():
    _check_parsing_is_reversible("a.@!2?")

def test__parse_sopheme_sequence__multiple_sophemes():
    _check_parsing_is_reversible("h.h y.ae!1 d.d r.r o.@ g.jh e.E5 n.n")

def test__parse_sopheme_sequence__keysymbol_groups():
    _check_parsing_is_reversible("a.a n.ng x.(g z) i.ae!1 e.@ t.t y.iy")