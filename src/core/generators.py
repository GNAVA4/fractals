import math
from itertools import chain
from typing import Generator
from .types import Point, Line

# ───────────── СЕРПИНСКИЙ ─────────────
_CANONICAL_SIERPINSKI = (Point(0.0, 1.0), Point(-math.sqrt(3)/2, -0.5), Point(math.sqrt(3)/2, -0.5))

def _sierpinski_rec(depth: int, p1: Point, p2: Point, p3: Point) -> list[Line]:
    if depth == 0: return [Line(p1, p2), Line(p2, p3), Line(p3, p1)]
    m_ab = Point((p1.x + p2.x)/2, (p1.y + p2.y)/2)
    m_bc = Point((p2.x + p3.x)/2, (p2.y + p3.y)/2)
    m_ca = Point((p3.x + p1.x)/2, (p3.y + p1.y)/2)
    return list(chain(
        _sierpinski_rec(depth-1, p1, m_ab, m_ca),
        _sierpinski_rec(depth-1, m_ab, p2, m_bc),
        _sierpinski_rec(depth-1, m_ca, m_bc, p3)
    ))

def sierpinski_lines(depth: int) -> list[Line]:
    return _sierpinski_rec(depth, *_CANONICAL_SIERPINSKI)

# ───────────── T-ФРАКТАЛ ─────────────
def _t_rec(depth: int, start: Point, angle: float, length: float, scale: float) -> list[Line]:
    if depth == 0:
        rad = math.radians(angle)
        return [Line(start, Point(start.x + length*math.cos(rad), start.y + length*math.sin(rad)))]
    rad = math.radians(angle)
    end = Point(start.x + length*math.cos(rad), start.y + length*math.sin(rad))
    return list(chain.from_iterable(
        _t_rec(depth-1, end, angle + d, length*scale, scale) for d in (-90.0, 0.0, 90.0)
    ))

def t_fractal_lines(depth: int, scale: float = 0.5) -> list[Line]:
    return _t_rec(depth, Point(0, 0), 90.0, 1.0, scale)

# ───────────── H-ФРАКТАЛ ─────────────
def _h_rec(depth: int, center: Point, size: float, scale: float, vertical: bool) -> list[Line]:
    if depth == 0: return []
    if vertical:
        line = Line(Point(center.x, center.y-size/2), Point(center.x, center.y+size/2))
        nc = (Point(center.x, center.y-size/2), Point(center.x, center.y+size/2))
    else:
        line = Line(Point(center.x-size/2, center.y), Point(center.x+size/2, center.y))
        nc = (Point(center.x-size/2, center.y), Point(center.x+size/2, center.y))
    return [line] + list(chain.from_iterable(_h_rec(depth-1, c, size*scale, scale, not vertical) for c in nc))

def h_fractal_lines(depth: int, scale: float = 0.5) -> list[Line]:
    return _h_rec(depth, Point(0, 0), 1.0, scale, True)

# ───────────── КОХ ─────────────
def _koch_rec(start: Point, end: Point, depth: int) -> list[Line]:
    if depth == 0: return [Line(start, end)]
    dx, dy = end.x - start.x, end.y - start.y
    p2 = Point(start.x + dx/3, start.y + dy/3)
    p4 = Point(start.x + 2*dx/3, start.y + 2*dy/3)
    peak = Point(start.x + dx/2 - dy*math.sqrt(3)/6, start.y + dy/2 + dx*math.sqrt(3)/6)
    return list(chain(
        _koch_rec(start, p2, depth-1), _koch_rec(p2, peak, depth-1),
        _koch_rec(peak, p4, depth-1), _koch_rec(p4, end, depth-1)
    ))

def koch_lines(depth: int) -> list[Line]:
    return _koch_rec(Point(-0.6, -0.2), Point(0.6, -0.2), depth)

# ───────────── ДЕРЕВО ─────────────
def _tree_rec(start: Point, angle: float, length: float, depth: int, spread: float, scale: float) -> list[Line]:
    if depth == 0 or length < 0.005: return []
    rad = math.radians(angle)
    end = Point(start.x + length*math.cos(rad), start.y + length*math.sin(rad))
    return [Line(start, end)] + list(chain(
        _tree_rec(end, angle - spread, length*scale, depth-1, spread, scale),
        _tree_rec(end, angle + spread, length*scale, depth-1, spread, scale)
    ))

def tree_lines(depth: int, scale: float = 0.75, spread: float = 25.0) -> list[Line]:
    return _tree_rec(Point(0, -0.5), 90.0, 1.0, depth, spread, scale)

# ───────────── ИТЕРАТИВНАЯ ГЕНЕРАЦИЯ ПО БАТЧАМ ─────────────


def sierpinski_batches(depth: int) -> Generator[list[Line], None, None]:
    """Серпинский: линии группами по 3 (один маленький треугольник) за батч."""
    all_lines = sierpinski_lines(depth)
    group_size = max(1, len(all_lines) // max(depth * 4, 5))
    for i in range(0, len(all_lines), group_size):
        yield list(all_lines[i:i + group_size])


def t_fractal_batches(depth: int, scale: float = 0.5) -> Generator[list[Line], None, None]:
    """T-фрактал по уровням через BFS — каждый батч добавляет новый уровень."""
    queue: list[tuple[Point, float, float]] = [(Point(0, 0), 90.0, 1.0)]

    for _ in range(depth):
        next_queue: list[tuple[Point, float, float]] = []
        batch: list[Line] = []
        for start, angle_deg, length in queue:
            rad = math.radians(angle_deg)
            end = Point(start.x + length*math.cos(rad), start.y + length*math.sin(rad))
            batch.append(Line(start, end))
            next_queue.extend([
                (end, angle_deg - 90.0, length * scale),
                (end, angle_deg + 0.0, length * scale),
                (end, angle_deg + 90.0, length * scale)
            ])
        yield batch
        queue = next_queue


def h_fractal_batches(depth: int, scale: float = 0.5) -> Generator[list[Line], None, None]:
    """H-фрактал по уровням — каждый батч добавляет новый уровень."""
    nodes: list[tuple[Point, float, str]] = [(Point(0, 0), 1.0, 'v')]

    for _ in range(depth):
        level_lines: list[Line] = []
        new_nodes: list[tuple[Point, float, str]] = []
        for center, size, orientation in nodes:
            if orientation == 'v':
                top = Point(center.x, center.y - size/2)
                bot = Point(center.x, center.y + size/2)
                level_lines.append(Line(top, bot))
                new_nodes.extend([(top, size*scale, 'h'), (bot, size*scale, 'h')])
            else:
                left = Point(center.x - size/2, center.y)
                right = Point(center.x + size/2, center.y)
                level_lines.append(Line(left, right))
                new_nodes.extend([(left, size*scale, 'v'), (right, size*scale, 'v')])
        yield level_lines
        nodes = new_nodes


def koch_batches(depth: int) -> Generator[list[Line], None, None]:
    """Кривая Коха по уровням — каждый батч показывает subdivision одного уровня."""
    queue = [(Point(-0.6, -0.2), Point(0.6, -0.2), 0)]

    while any(d < depth for _, _, d in queue):
        batch = []
        new_queue = []
        for start, end, d in queue:
            if d == depth:
                new_queue.append((start, end, depth))
                continue
            dx, dy = end.x - start.x, end.y - start.y
            p2 = Point(start.x + dx/3, start.y + dy/3)
            p4 = Point(start.x + 2*dx/3, start.y + 2*dy/3)
            peak = Point(start.x + dx/2 - dy*math.sqrt(3)/6, start.y + dy/2 + dx*math.sqrt(3)/6)
            batch.append(Line(start, p2))
            batch.append(Line(p2, peak))
            batch.append(Line(peak, p4))
            batch.append(Line(p4, end))
            new_queue.extend([(start, p2, d+1), (p2, peak, d+1), (peak, p4, d+1), (p4, end, d+1)])
        yield batch
        queue = new_queue


def tree_batches(depth: int, scale: float = 0.75, spread: float = 25.0) -> Generator[list[Line], None, None]:
    """Дерево по уровням — каждый батч добавляет новый уровень ветвей."""
    current: list[tuple[Point, float, float]] = [(Point(0, -0.5), 90.0, 1.0)]

    for level in range(depth):
        next_level: list[tuple[Point, float, float]] = []
        batch: list[Line] = []
        for start, angle_deg, length in current:
            if length < 0.005:
                continue
            rad = math.radians(angle_deg)
            end = Point(start.x + length*math.cos(rad), start.y + length*math.sin(rad))
            batch.append(Line(start, end))
            if level < depth - 1:
                next_level.extend([
                    (end, angle_deg - spread, length * scale),
                    (end, angle_deg + spread, length * scale)
                ])
        yield batch
        current = next_level


def lightning_batches(depth: int, seed: int = 42, roughness: float = 0.8) -> Generator[list[Line], None, None]:
    """Молния по уровням рекурсии (BFS)."""
    queue: list[tuple[Point, Point, int]] = [(Point(0.0, 0.0), Point(1.0, 0.0), depth)]

    while queue:
        batch: list[Line] = []
        next_queue: list[tuple[Point, Point, int]] = []
        for start, end, d in queue:
            if d == 0:
                batch.append(Line(start, end))
            else:
                mid = Point((start.x + end.x)/2, (start.y + end.y)/2)
                dx, dy = end.x - start.x, end.y - start.y
                length = math.hypot(dx, dy)
                if length < 1e-6:
                    batch.append(Line(start, end))
                else:
                    perp_x, perp_y = -dy/length, dx/length
                    noise_val = math.sin(seed * 12.9898 + d * 78.233) * 43758.5453
                    noise_val = 2.0 * (noise_val - math.floor(noise_val)) - 1.0
                    offset = noise_val * roughness * length / (2**d)
                    new_mid = Point(mid.x + perp_x*offset, mid.y + perp_y*offset)
                    next_queue.extend([(start, new_mid, d-1), (new_mid, end, d-1)])
        if batch:
            yield batch
        queue = next_queue
