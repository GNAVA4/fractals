from functools import reduce
from itertools import chain
from typing import Callable, TypeVar, Iterable
from .types import Line

T = TypeVar("T")

def compose(*funcs: Callable[[T], T]) -> Callable[[T], T]:
    """Композиция функций: compose(f, g, h)(x) == f(g(h(x)))"""
    def composed(arg: T) -> T:
        return reduce(lambda acc, f: f(acc), reversed(funcs), arg)
    return composed

def apply_to_lines(lines: Iterable[Line], *transforms: Callable[[Line], Line]) -> list[Line]:
    """Применяет цепочку трансформаций ко всем линиям."""
    if not transforms:
        return list(lines)
    transform_chain = compose(*transforms)
    return [transform_chain(line) for line in lines]

def flatten_lines(nested: Iterable[Iterable[Line]]) -> list[Line]:
    """Превращает вложенные списки линий в плоский список (без побочных эффектов)."""
    return list(chain.from_iterable(nested))