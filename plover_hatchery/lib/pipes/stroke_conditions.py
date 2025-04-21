from plover.steno import Stroke


def if_stroke_has_overlap_with(stroke_or_steno_1: "Stroke | str"):
    stroke_1 = Stroke.from_steno(stroke_or_steno_1) if isinstance(stroke_or_steno_1, str) else stroke_or_steno_1

    def check(stroke_2: Stroke):
        return len(stroke_1 & stroke_2) > 0
    
    return check


def always(stroke: Stroke):
    return True