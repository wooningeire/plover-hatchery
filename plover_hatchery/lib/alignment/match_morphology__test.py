from plover_hatchery.lib.alignment.match_morphology import match_morphology_to_chars
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


def test__match_morphology_to_chars__assigns_orthography_without_losing_chunks() -> None:
    morphology = split_morphology(
        "< u n < { d ou } > i ng >",
        "<un<{do}>ing>",
    )

    matched = match_morphology_to_chars(morphology, "undoing")

    assert _describe_chunks(matched) == (
        (Affix, False, (("un", "u n", "un"),)),
        (Root, None, (("do", "d ou", "do"),)),
        (Affix, True, (("ing", "i ng", "ing"),)),
    )
