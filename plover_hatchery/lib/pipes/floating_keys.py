from typing import Any, Generator


from dataclasses import dataclass

from plover.steno import Stroke

from .Plugin import Plugin, define_plugin


@dataclass
class FloatingKeysApi:
    floaters: Stroke

    def can_add_stroke_on(self, src_stroke: Stroke, addon_stroke: Stroke) -> bool:
        src_without_floaters = self.without_floaters(src_stroke)
        if len(src_without_floaters) == 0:
            return True

        addon_without_floaters = self.without_floaters(addon_stroke)
        if len(addon_without_floaters) == 0:
            return True

        last_key_of_src = Stroke.from_keys(((src_without_floaters).keys()[-1],))
        first_key_of_addon = Stroke.from_keys(((addon_without_floaters).keys()[0],))

        return last_key_of_src < first_key_of_addon


    def without_floaters(self, stroke: Stroke):
        return stroke - self.floaters

    def only_floaters(self, stroke: Stroke):
        return stroke & self.floaters

    def split(self, stroke: Stroke):
        return self.without_floaters(stroke), self.only_floaters(stroke)

    def stroke_keys_with_floating_last(self, stroke: Stroke) -> tuple[str, ...]:
        return (*self.without_floaters(stroke).keys(), *self.only_floaters(stroke).keys())


def floating_keys(floating_keys_steno: str) -> Plugin[FloatingKeysApi]:
    """
    Declares a set of keys as floating, or not abiding by stroke order, in such a way as to affect chords that use them.
    
    Usually includes the asterisk key `*`. This allows chords like `*T` not to require `*` and `-T` to appear consecutively in a stroke.
    """

    @define_plugin(floating_keys)
    def plugin(**_):
        return FloatingKeysApi(Stroke.from_steno(floating_keys_steno))

    return plugin