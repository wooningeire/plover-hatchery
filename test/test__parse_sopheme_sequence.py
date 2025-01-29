def test__parse_seq__single_sopheme():
    from plover_hatchery.lib.sopheme.parse import parse_sopheme_sequence
    from plover_hatchery.lib.sopheme.Sopheme import Orthokeysymbol, Keysymbol

    assert (
        Orthokeysymbol.format_seq(parse_sopheme_sequence("a.@"))
        == Orthokeysymbol.format_seq((
            Orthokeysymbol(
                (
                    Keysymbol("@", "", 0, False),
                ),
                "a"
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