from typing import Any, Generator


from dataclasses import dataclass

from plover.steno import Stroke

from .Plugin import Plugin, define_plugin


@dataclass
class FloatingKeysApi:
    floaters: Stroke

    def can_add_stroke_on(self, src_stroke: Stroke, addon_stroke: Stroke) -> bool:
        return (
            len(src_stroke - self.floaters) == 0
            or len(addon_stroke - self.floaters) == 0
            or Stroke.from_keys(((src_stroke - self.floaters).keys()[-1],)) < Stroke.from_keys(((addon_stroke - self.floaters).keys()[0],))
        )

    def without_floaters(self, stroke: Stroke):
        return stroke - self.floaters

    def only_floaters(self, stroke: Stroke):
        return stroke & self.floaters

    def split(self, stroke: Stroke):
        return self.without_floaters(stroke), self.only_floaters(stroke)

    def stroke_keys_with_floating_last(self, stroke: Stroke) -> tuple[str, ...]:
        return (*self.without_floaters(stroke).keys(), *self.only_floaters(stroke).keys())


def floating_keys(floating_keys_steno: str) -> Plugin[FloatingKeysApi]:
    """Declares a set of keys as floating, or not abiding by stroke key order in a meaningful way. Usually includes the asterisk key `*`."""

    @define_plugin(floating_keys)
    def plugin(**_):
        return FloatingKeysApi(Stroke.from_steno(floating_keys_steno))

    return plugin