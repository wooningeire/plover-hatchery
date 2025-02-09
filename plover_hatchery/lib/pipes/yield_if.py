from collections.abc import Generator
from typing import TypeVar

from plover.steno import Stroke


T = TypeVar("T")

def yield_if(condition: bool, value: T) -> Generator[T, None, None]:
    if not condition: return
    yield value

def yield_stroke_if(condition: bool, steno: str) -> Generator[Stroke, None, None]:
    if not condition: return
    yield Stroke.from_steno(steno)