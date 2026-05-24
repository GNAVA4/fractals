"""
Генераторы фракталов.

Контракт: `*_lines(...)` и `*_batches(...)` ВСЕГДА выдают линии в одном
и том же порядке (просто batches разбит на группы). Это критично для
индексной раскраски: цвет линии в финале и в анимации совпадает.

Реализовано так:
- Регулярные фракталы (sierpinski, koch, lightning): `*_lines` — primary,
  `*_batches` чанкует результат.
- Рекурсивные с накоплением по уровням (tree, t_fractal, h_fractal):
  `*_batches` — primary (BFS, по уровням), `*_lines` свёртывает их.
"""
import math
from itertools import chain
from typing import Generator
from .types import Point, Line


# ───────────── СЕРПИНСКИЙ ─────────────
_CANONICAL_SIERPINSKI = (Point(0.0, 1.0), Point(-math.sqrt(3) / 2, -0.5), Point(math.sqrt(3) / 2, -0.5))


def _sierpinski_rec(depth: int, p1: Point, p2: Point, p3: Point) -> list[Line]:
    if depth == 0:
        return [Line(p1, p2), Line(p2, p3), Line(p3, p1)]
    m_ab = Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2)
    m_bc = Point((p2.x + p3.x) / 2, (p2.y + p3.y) / 2)
    m_ca = Point((p3.x + p1.x) / 2, (p3.y + p1.y) / 2)
    return list(chain(
        _sierpinski_rec(depth - 1, p1, m_ab, m_ca),
        _sierpinski_rec(depth - 1, m_ab, p2, m_bc),
        _sierpinski_rec(depth - 1, m_ca, m_bc, p3),
    ))


def sierpinski_lines(depth: int) -> list[Line]:
    return _sierpinski_rec(depth, *_CANONICAL_SIERPINSKI)


def sierpinski_batches(depth: int) -> Generator[list[Line], None, None]:
    """Линии группами для прогрессивной анимации."""
    all_lines = sierpinski_lines(depth)
    group_size = max(1, len(all_lines) // max(depth * 4, 5))
    for i in range(0, len(all_lines), group_size):
        yield all_lines[i:i + group_size]


# ───────────── КОХ ─────────────
def _koch_rec(start: Point, end: Point, depth: int) -> list[Line]:
    if depth == 0:
        return [Line(start, end)]
    dx, dy = end.x - start.x, end.y - start.y
    p2 = Point(start.x + dx / 3, start.y + dy / 3)
    p4 = Point(start.x + 2 * dx / 3, start.y + 2 * dy / 3)
    peak = Point(start.x + dx / 2 - dy * math.sqrt(3) / 6,
                 start.y + dy / 2 + dx * math.sqrt(3) / 6)
    return list(chain(
        _koch_rec(start, p2, depth - 1),
        _koch_rec(p2, peak, depth - 1),
        _koch_rec(peak, p4, depth - 1),
        _koch_rec(p4, end, depth - 1),
    ))


def koch_lines(depth: int) -> list[Line]:
    return _koch_rec(Point(-0.6, -0.2), Point(0.6, -0.2), depth)


def koch_batches(depth: int) -> Generator[list[Line], None, None]:
    all_lines = koch_lines(depth)
    if not all_lines:
        return
    chunk_size = max(1, len(all_lines) // max(depth * 4, 6))
    for i in range(0, len(all_lines), chunk_size):
        yield all_lines[i:i + chunk_size]


# ───────────── T-ФРАКТАЛ ─────────────
def t_fractal_batches(depth: int, scale: float = 0.5) -> Generator[list[Line], None, None]:
    """BFS по уровням. Каждый батч = один уровень рекурсии."""
    queue: list[tuple[Point, float, float]] = [(Point(0.0, 0.0), 90.0, 1.0)]
    for _ in range(depth):
        next_queue: list[tuple[Point, float, float]] = []
        batch: list[Line] = []
        for start, angle_deg, length in queue:
            rad = math.radians(angle_deg)
            end = Point(start.x + length * math.cos(rad), start.y + length * math.sin(rad))
            batch.append(Line(start, end))
            next_queue.extend([
                (end, angle_deg - 90.0, length * scale),
                (end, angle_deg + 0.0, length * scale),
                (end, angle_deg + 90.0, length * scale),
            ])
        yield batch
        queue = next_queue


def t_fractal_lines(depth: int, scale: float = 0.5) -> list[Line]:
    return list(chain.from_iterable(t_fractal_batches(depth, scale)))


# ───────────── H-ФРАКТАЛ ─────────────
def h_fractal_batches(depth: int, scale: float = 0.5) -> Generator[list[Line], None, None]:
    """BFS по уровням. Каждый батч = новый уровень H-сегментов."""
    nodes: list[tuple[Point, float, str]] = [(Point(0.0, 0.0), 1.0, 'v')]
    for _ in range(depth):
        level_lines: list[Line] = []
        new_nodes: list[tuple[Point, float, str]] = []
        for center, size, orientation in nodes:
            if orientation == 'v':
                top = Point(center.x, center.y - size / 2)
                bot = Point(center.x, center.y + size / 2)
                level_lines.append(Line(top, bot))
                new_nodes.extend([(top, size * scale, 'h'), (bot, size * scale, 'h')])
            else:
                left = Point(center.x - size / 2, center.y)
                right = Point(center.x + size / 2, center.y)
                level_lines.append(Line(left, right))
                new_nodes.extend([(left, size * scale, 'v'), (right, size * scale, 'v')])
        yield level_lines
        nodes = new_nodes


def h_fractal_lines(depth: int, scale: float = 0.5) -> list[Line]:
    return list(chain.from_iterable(h_fractal_batches(depth, scale)))


# ───────────── ДЕРЕВО ─────────────
def tree_batches(depth: int, scale: float = 0.75, spread: float = 25.0) -> Generator[list[Line], None, None]:
    """BFS по уровням: ствол -> ветви -> подветви ..."""
    current: list[tuple[Point, float, float]] = [(Point(0.0, -0.5), 90.0, 1.0)]
    for level in range(depth):
        next_level: list[tuple[Point, float, float]] = []
        batch: list[Line] = []
        for start, angle_deg, length in current:
            if length < 0.005:
                continue
            rad = math.radians(angle_deg)
            end = Point(start.x + length * math.cos(rad), start.y + length * math.sin(rad))
            batch.append(Line(start, end))
            if level < depth - 1:
                next_level.extend([
                    (end, angle_deg - spread, length * scale),
                    (end, angle_deg + spread, length * scale),
                ])
        yield batch
        current = next_level


def tree_lines(depth: int, scale: float = 0.75, spread: float = 25.0) -> list[Line]:
    return list(chain.from_iterable(tree_batches(depth, scale, spread)))


# ───────────── МОЛНИЯ ─────────────
def lightning_batches(depth: int, seed: int = 42, roughness: float = 0.8) -> Generator[list[Line], None, None]:
    """Чанкование готовой молнии (см. lightning.py для алгоритма)."""
    from .lightning import lightning_lines
    all_lines = lightning_lines(depth, seed, roughness)
    if not all_lines:
        return
    chunk_size = max(1, len(all_lines) // max(depth * 2, 6))
    for i in range(0, len(all_lines), chunk_size):
        yield all_lines[i:i + chunk_size]
