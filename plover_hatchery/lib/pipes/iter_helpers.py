from collections.abc import Generator, Iterable
from typing import Any, Callable, Generator, TypeVar

from plover.steno import Stroke

K = TypeVar("K")
V = TypeVar("V")


def take_first_nonempty_iterable(*seqs: Iterable[V]) -> Generator[V, None, None]:
    for seq in seqs:
        iterator = iter(seq)
        
        try:
            yield next(iterator)
        except StopIteration:
            continue
            
        yield from iterator
        return


def take_first_match(*generators: Callable[[K], Iterable[V]]):
    """Yields from the result of the first generator with a nonempty output."""

    def generate(key: K) -> Generator[V, None, None]:
        yield from take_first_nonempty_iterable(*(generator(key) for generator in generators))
    
    return generate


def yield_if(predicate: Callable[[K], bool], values: Callable[[K], Iterable[V]]):
    def generate(key: K) -> Generator[V, None, None]:
        if not predicate(key): return
        yield from values(key)

    return generate

def chords(stenos: str):
    strokes = tuple(Stroke.from_steno(steno) for steno in stenos.split())

    def generate(_: Any):
        return strokes
    
    return generate


def if_all(*predicates: Callable[[K], bool]):
    def check(key: K):
        return all(condition(key) for condition in predicates)
    
    return check


def if_any(*predicates: Callable[[K], bool]):
    def check(key: K):
        return any(condition(key) for condition in predicates)
    
    return check


def if_not(predicate: Callable[[K], bool]):
    def check(key: K):
        return not predicate(key)
    
    return check