"""
Мост между ядром (чистая логика) и GUI.
Превращает FractalConfig в готовые цветные линии (один проход или итератор батчей).
"""
from typing import Callable, Iterator
from .core.types import FractalConfig, Point, Line
from .core import generators, lightning
from .core.symmetry import apply_symmetries, reflect_x, reflect_y, radial_symmetry
from .core.transforms import scale, rotate
from .core.coloring import colorize_lines, ColorParams
from .core.utils import compose


_FULL_GENERATORS: dict[str, Callable[[FractalConfig], list[Line]]] = {
    "sierpinski": lambda c: generators.sierpinski_lines(c.depth),
    "t_fractal":  lambda c: generators.t_fractal_lines(c.depth, c.scale),
    "h_fractal":  lambda c: generators.h_fractal_lines(c.depth, c.scale),
    "koch":       lambda c: generators.koch_lines(c.depth),
    "tree":       lambda c: generators.tree_lines(c.depth, c.scale, c.tree_spread),
    "lightning":  lambda c: lightning.lightning_lines(c.depth, c.seed, c.roughness),
}

_BATCH_GENERATORS: dict[str, Callable[[FractalConfig], Iterator[list[Line]]]] = {
    "sierpinski": lambda c: generators.sierpinski_batches(c.depth),
    "t_fractal":  lambda c: generators.t_fractal_batches(c.depth, c.scale),
    "h_fractal":  lambda c: generators.h_fractal_batches(c.depth, c.scale),
    "koch":       lambda c: generators.koch_batches(c.depth),
    "tree":       lambda c: generators.tree_batches(c.depth, c.scale, c.tree_spread),
    "lightning":  lambda c: generators.lightning_batches(c.depth, c.seed, c.roughness),
}


def _build_transform(config: FractalConfig) -> Callable[[Line], Line]:
    """Свёртка двух аффинных трансформаций (scale ∘ rotate) в одну функцию."""
    origin = Point(0.0, 0.0)
    return compose(
        lambda l: rotate(l, config.rotation_deg, origin),
        lambda l: scale(l, config.display_scale, origin),
    )


def _build_symmetries(config: FractalConfig):
    syms = []
    if config.symmetry_x:
        syms.append(reflect_x)
    if config.symmetry_y:
        syms.append(reflect_y)
    if config.radial_symmetry > 1:
        syms.append(radial_symmetry(config.radial_symmetry))
    return syms


def _gen_raw(config: FractalConfig) -> list[Line]:
    try:
        return _FULL_GENERATORS[config.fractal_type](config)
    except KeyError:
        raise ValueError(f"Unknown fractal type: {config.fractal_type}")


def generate_fractal(config: FractalConfig) -> list[tuple[Line, str]]:
    """Полная генерация: raw -> transform -> symmetries -> colorize."""
    raw = _gen_raw(config)
    transform = _build_transform(config)
    transformed = [transform(l) for l in raw]
    final = apply_symmetries(transformed, *_build_symmetries(config))
    return colorize_lines(final, config.color_mode, config.seed)


def generate_fractal_batched(
    config: FractalConfig,
) -> Iterator[tuple[list[tuple[Line, str]], int, int]]:
    """
    Возвращает (colored_lines_batch, batch_idx, total_batches).
    Симметрии и нормализация цвета считаются ОДИН раз по полному фракталу,
    чтобы цвета не «дёргались» между кадрами.
    """
    try:
        batch_fn = _BATCH_GENERATORS[config.fractal_type]
    except KeyError:
        raise ValueError(f"Unknown fractal type: {config.fractal_type}")

    transform = _build_transform(config)
    syms = _build_symmetries(config)

    batches_raw: list[list[Line]] = [list(b) for b in batch_fn(config)]
    batches_transformed = [
        apply_symmetries([transform(l) for l in batch], *syms) for batch in batches_raw
    ]
    total_lines = sum(len(b) for b in batches_transformed)

    total_batches = len(batches_transformed)
    offset = 0
    for idx, batch in enumerate(batches_transformed):
        params = ColorParams(total=total_lines, index_offset=offset, seed=config.seed)
        yield colorize_lines(batch, config.color_mode, config.seed, params), idx, total_batches
        offset += len(batch)
