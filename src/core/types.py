from dataclasses import dataclass
from typing import Protocol, Iterable

@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float

@dataclass(frozen=True, slots=True)
class Line:
    start: Point
    end: Point

@dataclass(frozen=True, slots=True)
class FractalConfig:
    fractal_type: str = "sierpinski"
    depth: int = 3
    scale: float = 0.5
    display_scale: float = 300.0
    rotation_deg: float = 0.0
    translation: tuple[float, float] = (0.0, 0.0)
    line_width: float = 1.5
    color_mode: str = "gradient"
    tree_spread: float = 25.0      # Угол ветвления дерева
    seed: int = 42
    roughness: float = 0.8
    symmetry_x: bool = False
    symmetry_y: bool = False
    radial_symmetry: int = 0

class SymmetryFunc(Protocol):
    def __call__(self, line: Line) -> Iterable[Line]: ...