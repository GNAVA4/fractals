from dataclasses import dataclass
from typing import Literal

FractalType = Literal["sierpinski", "t_fractal", "h_fractal", "koch", "tree", "lightning"]
ColorMode = Literal[
    "ocean", "fire", "forest", "cosmic", "aurora", "sunset", "neon", "mono", "rainbow",
    "gradient", "pos",  # legacy aliases
]


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
    fractal_type: FractalType = "sierpinski"
    depth: int = 3
    scale: float = 0.5
    display_scale: float = 300.0
    rotation_deg: float = 0.0
    line_width: float = 1.5
    color_mode: ColorMode = "aurora"
    tree_spread: float = 25.0
    seed: int = 42
    roughness: float = 0.8
    symmetry_x: bool = False
    symmetry_y: bool = False
    radial_symmetry: int = 0
