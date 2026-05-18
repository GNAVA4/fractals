import math
from typing import Callable, Iterable
from itertools import chain
from .types import Point, Line

# Базовые симметрии
def reflect_x(line: Line) -> list[Line]:
    """Возвращает оригинал и отражённую копию."""
    return [line, Line(Point(line.start.x, -line.start.y), Point(line.end.x, -line.end.y))]

def reflect_y(line: Line) -> list[Line]:
    """Возвращает оригинал и отражённую копию."""
    return [line, Line(Point(-line.start.x, line.start.y), Point(-line.end.x, line.end.y))]

def radial_symmetry(n: int, center: Point = Point(0, 0)) -> Callable[[Line], Iterable[Line]]:
    """Возвращает функцию, создающую n-кратную радиальную симметрию"""
    if n < 1:
        raise ValueError("n must be >= 1")
    angle_step = 360.0 / n
    cos_s, sin_s = math.cos(math.radians(angle_step)), math.sin(math.radians(angle_step))
    
    def apply(line: Line) -> Iterable[Line]:
        cs, ce = line.start, line.end
        yield Line(cs, ce)  # оригинал
        for _ in range(n - 1):
            # Поворот точки вокруг центра
            def rotate(p: Point) -> Point:
                dx, dy = p.x - center.x, p.y - center.y
                return Point(center.x + dx*cos_s - dy*sin_s,
                             center.y + dx*sin_s + dy*cos_s)
            cs, ce = rotate(cs), rotate(ce)
            yield Line(cs, ce)
    return apply

# Композиция симметрий
def apply_symmetries(lines: Iterable[Line], *syms: Callable[[Line], Iterable[Line]]) -> list[Line]:
    """Применяет набор симметрий к списку линий. Чистая функция-комбинатор."""
    if not syms:
        return list(lines)
    
    # Каждая функция симметрии должна вернуть [original, ...copies]
    # Применяем все симметрии независимо и объединяем результаты
    result = []
    for line in lines:
        seen = set()
        for sym in syms:
            for sym_line in sym(line):
                key = (sym_line.start.x, sym_line.start.y, sym_line.end.x, sym_line.end.y)
                if key not in seen:
                    seen.add(key)
                    result.append(sym_line)
    return result