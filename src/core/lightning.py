import math
from .types import Point, Line

def _pure_noise(seed: int, depth: int, idx: int) -> float:
    """Детерминированный чистый шум в диапазоне [-1, 1]"""
    val = math.sin(seed * 12.9898 + depth * 78.233 + idx * 45.164) * 43758.5453
    return 2.0 * (val - math.floor(val)) - 1.0

def _generate_lightning_rec(start: Point, end: Point, depth: int, seed: int, roughness: float, idx: int = 0) -> list[Line]:
    if depth == 0:
        return [Line(start, end)]

    mid = Point((start.x + end.x) / 2, (start.y + end.y) / 2)
    dx, dy = end.x - start.x, end.y - start.y
    length = math.hypot(dx, dy)

    if length < 1e-6:
        return [Line(start, end)]

    # Нормаль к отрезку
    perp_x, perp_y = -dy / length, dx / length

    # Чистое смещение средней точки
    noise = _pure_noise(seed, depth, idx)
    offset = noise * roughness * length / (2 ** depth)
    new_mid = Point(mid.x + perp_x * offset, mid.y + perp_y * offset)

    # Рекурсия для двух половинок
    left = _generate_lightning_rec(start, new_mid, depth - 1, seed, roughness, idx * 2)
    right = _generate_lightning_rec(new_mid, end, depth - 1, seed, roughness, idx * 2 + 1)

    return left + right

def lightning_lines(depth: int, seed: int = 42, roughness: float = 0.8) -> list[Line]:
    """Генерирует фрактальную молнию от (0,0) до (1,0)"""
    return _generate_lightning_rec(Point(0.0, 0.0), Point(1.0, 0.0), depth, seed, roughness)