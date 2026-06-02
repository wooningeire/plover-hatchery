from plover_hatchery.lib.alignment.parse_morphology import Affix, Morphology, Root, split_morphology


ChunkDescription = tuple[type[object], bool | None, tuple[tuple[str, str, str], ...]]


def _describe_chunks(morphology: Morphology) -> tuple[ChunkDescription, ...]:
    return tuple(
        (
            type(chunk),
            getattr(chunk, "is_suffix", None),
            tuple((part.name, part.phono, part.ortho) for part in chunk.parts()),
        )
        for chunk in morphology.chunks
    )


def test__split_morphology__splits_root_and_suffixes() -> None:
    morphology = split_morphology(
        " { * eir r }.> w ~ @@r r . dh == iy >.> E05 s t > ",
        "{air}>worth==y>>est>",
    )

    assert _describe_chunks(morphology) == (
        (Root, None, (("air", "* eir r", ""),)),
        (Affix, True, (("worth", "w ~ @@r r . dh", ""), ("y", "iy", ""))),
        (Affix, True, (("est", "E05 s t", ""),)),
    )


def test__split_morphology__splits_prefix_root_and_suffix() -> None:
    morphology = split_morphology(
        "< u n < { d ou } > i ng >",
        "<un<{do}>ing>",
    )

    assert _describe_chunks(morphology) == (
        (Affix, False, (("un", "u n", ""),)),
        (Root, None, (("do", "d ou", ""),)),
        (Affix, True, (("ing", "i ng", ""),)),
    )
