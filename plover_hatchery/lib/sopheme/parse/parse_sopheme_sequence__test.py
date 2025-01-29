def test__parse_sopheme_sequence__single_sopheme():
    from plover_hatchery.lib.sopheme.parse import parse_sopheme_sequence
    from plover_hatchery.lib.sopheme.Sopheme import Orthokeysymbol, Keysymbol

    assert (
        Orthokeysymbol.format_seq(parse_sopheme_sequence("a.@!2?"))
        == Orthokeysymbol.format_seq((
            Orthokeysymbol(
                (
                    Keysymbol("@", "", 2, True),
                ),
                "a"
            ),
        ))
    )

def test__parse_sopheme_sequence__multiple_sophemes():
    from plover_hatchery.lib.sopheme.parse import parse_sopheme_sequence
    from plover_hatchery.lib.sopheme.Sopheme import Orthokeysymbol, Keysymbol

    assert (
        Orthokeysymbol.format_seq(parse_sopheme_sequence("h.h y.ae!1 d.d r.r o.@ g.jh e.E5 n.n"))
        == Orthokeysymbol.format_seq((
            Orthokeysymbol(
                (
                    Keysymbol("h", "", 0, False),
                ),
                "h"
            ),
            Orthokeysymbol(
                (
                    Keysymbol("ae", "", 1, False),
                ),
                "y"
            ),
            Orthokeysymbol(
                (
                    Keysymbol("d", "", 0, False),
                ),
                "d"
            ),
            Orthokeysymbol(
                (
                    Keysymbol("r", "", 0, False),
                ),
                "r"
            ),
            Orthokeysymbol(
                (
                    Keysymbol("@", "", 0, False),
                ),
                "o"
            ),
            Orthokeysymbol(
                (
                    Keysymbol("jh", "", 0, False),
                ),
                "g"
            ),
            Orthokeysymbol(
                (
                    Keysymbol("E5", "", 0, False),
                ),
                "e"
            ),
            Orthokeysymbol(
                (
                    Keysymbol("n", "", 0, False),
                ),
                "n"
            ),
        ))
    )


    # sophemes = (
    #     Sopheme(
    #         (
    #             Orthokeysymbol(
    #                 (Keysymbol("z", "z"),), "z"
    #             ),
    #         ),
    #         (),
    #         Stenophoneme.Z,
    #     ),

    #     Sopheme(
    #         (
    #             Orthokeysymbol(
    #                 (Keysymbol("ou", "ou"),), "o"
    #             ),
    #         ),
    #         (),
    #         Stenophoneme.OO,
    #     ),
    # )

    # seq = " ".join(str(sopheme) for sopheme in sophemes)

    # print(parse_sopheme_seq("z.z[Z] o.ou[OO] d.d[D] i.ae!1[II] [[KWR]] a.@[A] c.k[K] [[KWR]] a.A5[A] l"))
    
    # assert (
    #     parse_sopheme_seq("z.z[Z] o.ou[OO] d.d[D] i.ae!1[II] [[KWR]] a.@[A] c.k[K] [[KWR]] a.A5[A] l")
    #     == (
            
    #     )
    # )