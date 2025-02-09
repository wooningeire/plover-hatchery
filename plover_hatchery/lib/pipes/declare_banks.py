from dataclasses import dataclass

from plover.steno import Stroke

from .Plugin import Plugin, define_plugin


@dataclass
class BankStrokes:
    left: Stroke
    mid: Stroke
    right: Stroke
    positionless: Stroke


    @property
    def all(self):
        return self.left + self.mid + self.right + self.positionless


    def split_stroke_parts(self, stroke: Stroke):
        left_bank_consonants = stroke & self.left
        vowels = stroke & self.mid
        right_bank_consonants = stroke & self.right
        asterisk = stroke & self.positionless

        return left_bank_consonants, vowels, right_bank_consonants, asterisk


    def can_add_stroke_on(self, src_stroke: Stroke, addon_stroke: Stroke) -> bool:
        return (
            len(src_stroke - self.positionless) == 0
            or len(addon_stroke - self.positionless) == 0
            or Stroke.from_keys(((src_stroke - self.positionless).keys()[-1],)) < Stroke.from_keys(((addon_stroke - self.positionless).keys()[0],))
        )


def declare_banks(*, left: str, mid: str, right: str, positionless: str) -> Plugin[BankStrokes]:
    @define_plugin(declare_banks)
    def plugin(**_):
        return BankStrokes(
            Stroke.from_steno(left),
            Stroke.from_steno(mid),
            Stroke.from_steno(right),
            Stroke.from_steno(positionless),
        )

    return plugin