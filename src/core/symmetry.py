"""
Симметрии как чистые функции Line -> Iterable[Line].

Контракт: каждая функция симметрии возвращает ТОЛЬКО новые копии (без оригинала).
Композиция симметрий в `apply_symmetries` сама добавляет оригинал и накапливает
орбиту группы. Так получается корректная диэдральная симметрия: для двух
отражений на выходе будет 4 линии (D2), для радиальной N + двух отражений — 4N (D_{2N}).
"""
import math
from typing import Callable, Iterable
from .types import Point, Line


def reflect_x(line: Line) -> Iterable[Line]:
    """Отражение по оси X (y -> -y). Возвращает одну новую линию."""
    yield Line(
        Point(line.start.x, -line.start.y),
        Point(line.end.x, -line.end.y),
    )


def reflect_y(line: Line) -> Iterable[Line]:
    """Отражение по оси Y (x -> -x). Возвращает одну новую линию."""
    yield Line(
        Point(-line.start.x, line.start.y),
        Point(-line.end.x, line.end.y),
    )


def radial_symmetry(n: int, center: Point = Point(0.0, 0.0)) -> Callable[[Line], Iterable[Line]]:
    """Возвращает функцию, дающую n-1 повёрнутых копий (без оригинала)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    angles = [2.0 * math.pi * k / n for k in range(1, n)]
    rotations = [(math.cos(a), math.sin(a)) for a in angles]

    def apply(line: Line) -> Iterable[Line]:
        for cos_a, sin_a in rotations:
            sx, sy = line.start.x - center.x, line.start.y - center.y
            ex, ey = line.end.x - center.x, line.end.y - center.y
            yield Line(
                Point(center.x + sx * cos_a - sy * sin_a,
                      center.y + sx * sin_a + sy * cos_a),
                Point(center.x + ex * cos_a - ey * sin_a,
                      center.y + ex * sin_a + ey * cos_a),
            )
    return apply


def apply_symmetries(
    lines: Iterable[Line],
    *syms: Callable[[Line], Iterable[Line]],
) -> list[Line]:
    """
    Композиция симметрий: накапливает орбиту группы.
    После каждой симметрии результирующее множество = (текущее) + (sym(текущее)).
    Так reflect_x ∘ reflect_y даёт 4 линии, radial(N) ∘ reflect_x — 2N линий.
    """
    result = list(lines)
    for sym in syms:
        copies = [out for ln in result for out in sym(ln)]
        result.extend(copies)
    return result
