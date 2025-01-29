def test__parse_sopheme_sequence__single_sopheme():
    from plover_hatchery.lib.sopheme.parse import parse_sopheme_sequence
    from plover_hatchery.lib.sopheme.Sopheme import Sopheme, Keysymbol

    assert (
        Sopheme.format_seq(parse_sopheme_sequence("a.@!2?"))
        == Sopheme.format_seq((
            Sopheme(
                (
                    Keysymbol("@", "", 2, True),
                ),
                "a"
            ),
        ))
    )

def test__parse_sopheme_sequence__multiple_sophemes():
    from plover_hatchery.lib.sopheme.parse import parse_sopheme_sequence
    from plover_hatchery.lib.sopheme.Sopheme import Sopheme, Keysymbol

    assert (
        Sopheme.format_seq(parse_sopheme_sequence("h.h y.ae!1 d.d r.r o.@ g.jh e.E5 n.n"))
        == Sopheme.format_seq((
            Sopheme(
                (
                    Keysymbol("h", "", 0, False),
                ),
                "h"
            ),
            Sopheme(
                (
                    Keysymbol("ae", "", 1, False),
                ),
                "y"
            ),
            Sopheme(
                (
                    Keysymbol("d", "", 0, False),
                ),
                "d"
            ),
            Sopheme(
                (
                    Keysymbol("r", "", 0, False),
                ),
                "r"
            ),
            Sopheme(
                (
                    Keysymbol("@", "", 0, False),
                ),
                "o"
            ),
            Sopheme(
                (
                    Keysymbol("jh", "", 0, False),
                ),
                "g"
            ),
            Sopheme(
                (
                    Keysymbol("E5", "", 0, False),
                ),
                "e"
            ),
            Sopheme(
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