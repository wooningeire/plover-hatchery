from plover_hatchery.lib.alignment.steno_annotations import AsteriskableKey, AnnotatedChord


def test__annotations_from_outline__marks_keys_from_asterisked_strokes() -> None:
    annotations = AsteriskableKey.annotations_from_outline("ST*/-F")

    assert tuple((annotation.key, annotation.asterisk) for annotation in annotations) == (
        ("S-", True),
        ("T-", True),
        ("-F", False),
    )


def test__keys_to_strokes__keeps_ordered_keys_in_one_stroke() -> None:
    strokes = AnnotatedChord.keys_to_strokes(("S-", "T-", "-F"), (False, True, False))

    assert tuple(stroke.rtfcre for stroke in strokes) == ("ST*F",)


def test__keys_to_strokes__starts_new_stroke_when_key_order_wraps() -> None:
    strokes = AnnotatedChord.keys_to_strokes(("S-", "-F", "T-"), (False, False, False))

    assert tuple(stroke.rtfcre for stroke in strokes) == ("S-F", "T")
