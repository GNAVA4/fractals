import math
from .types import Point, Line

def _rotate_point(p: Point, angle_deg: float, center: Point) -> Point:
    rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    dx, dy = p.x - center.x, p.y - center.y
    return Point(
        x=center.x + dx * cos_a - dy * sin_a,
        y=center.y + dx * sin_a + dy * cos_a
    )

def translate(line: Line, dx: float, dy: float) -> Line:
    return Line(
        Point(line.start.x + dx, line.start.y + dy),
        Point(line.end.x + dx, line.end.y + dy)
    )

def rotate(line: Line, angle_deg: float, center: Point) -> Line:
    return Line(
        _rotate_point(line.start, angle_deg, center),
        _rotate_point(line.end, angle_deg, center)
    )

def scale(line: Line, factor: float, origin: Point) -> Line:
    return Line(
        Point(origin.x + (line.start.x - origin.x) * factor,
              origin.y + (line.start.y - origin.y) * factor),
        Point(origin.x + (line.end.x - origin.x) * factor,
              origin.y + (line.end.y - origin.y) * factor)
    )