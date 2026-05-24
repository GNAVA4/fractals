"""Демо-скрипт: проверка моста на разных конфигах."""
from src.core.types import FractalConfig
from src.bridge import generate_fractal

configs = [
    FractalConfig(fractal_type="sierpinski", depth=4, display_scale=250),
    FractalConfig(fractal_type="t_fractal", depth=5, scale=0.6, display_scale=200),
    FractalConfig(fractal_type="h_fractal", depth=4, display_scale=180),
    FractalConfig(fractal_type="lightning", depth=6, seed=123, roughness=0.7, display_scale=300),
    FractalConfig(fractal_type="h_fractal", depth=3, display_scale=150, symmetry_x=True, radial_symmetry=4),
]

for i, cfg in enumerate(configs, 1):
    lines = generate_fractal(cfg)
    print(f"[OK] config {i} ({cfg.fractal_type}): {len(lines)} lines")
    assert len(lines) > 0, "Generator returned empty list"

print("\nBridge OK.")
