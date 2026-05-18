from .core.types import FractalConfig, Point
from .core import generators, lightning
from .core.symmetry import apply_symmetries, reflect_x, reflect_y, radial_symmetry
from .core.utils import apply_to_lines
from .core.transforms import scale, rotate, translate
from .core.coloring import colorize_lines

def generate_fractal(config: FractalConfig) -> list[tuple[object, str]]:
    match config.fractal_type:
        case "sierpinski": lines = generators.sierpinski_lines(config.depth)
        case "t_fractal": lines = generators.t_fractal_lines(config.depth, config.scale)
        case "h_fractal": lines = generators.h_fractal_lines(config.depth, config.scale)
        case "koch": lines = generators.koch_lines(config.depth)
        case "tree": lines = generators.tree_lines(config.depth, config.scale, config.tree_spread)
        case "lightning": lines = lightning.lightning_lines(config.depth, config.seed, config.roughness)
        case _: raise ValueError(f"Unknown type: {config.fractal_type}")

    origin = Point(0.0, 0.0)
    transforms = [
        lambda l: scale(l, config.display_scale, origin),
        lambda l: rotate(l, config.rotation_deg, origin),
        lambda l: translate(l, config.translation[0], config.translation[1])
    ]
    transformed = apply_to_lines(lines, *transforms)

    sym_funcs = []
    if config.symmetry_x: sym_funcs.append(reflect_x)
    if config.symmetry_y: sym_funcs.append(reflect_y)
    if config.radial_symmetry > 1: sym_funcs.append(radial_symmetry(config.radial_symmetry))
    
    final = apply_symmetries(transformed, *sym_funcs) if sym_funcs else transformed
    return colorize_lines(final, config.color_mode, config.seed)


def _get_batch_fn(fractal_type: str):
    match fractal_type:
        case "sierpinski": return lambda c: generators.sierpinski_batches(c.depth)
        case "t_fractal": return lambda c: generators.t_fractal_batches(c.depth, c.scale)
        case "h_fractal": return lambda c: generators.h_fractal_batches(c.depth, c.scale)
        case "koch": return lambda c: generators.koch_batches(c.depth)
        case "tree": return lambda c: generators.tree_batches(c.depth, c.scale, c.tree_spread)
        case "lightning": return lambda c: generators.lightning_batches(c.depth, c.seed, c.roughness)
        case _: raise ValueError(f"Unknown type: {fractal_type}")


# Режимы анимации для каждого типа фрактала
# Все типы используют accumulate — каждый батч добавляет линии к предыдущим
_ACCUMULATE = {"sierpinski", "t_fractal", "h_fractal", "koch", "tree", "lightning"}

def generate_fractal_batched(config: FractalConfig):
    """
    Возвращает итератор батчей для анимации.
    
    Каждый элемент кортеж: (colored_lines, batch_idx, total_batches, mode)
    - colored_lines: list[tuple[Line, str]] — раскрашенные линии
    - batch_idx: int — индекс текущего батча
    - total_batches: int — общее число батчей  
    - mode: 'accumulate' | 'replace' — накапливать или заменять
    
    Для accumulate: canvas показывает все накопленные линии до current_batch_idx включительно.
    Для replace: canvas показывает только lines из текущего батча.
    """
    origin = Point(0.0, 0.0)
    transforms = [
        lambda l: scale(l, config.display_scale, origin),
        lambda l: rotate(l, config.rotation_deg, origin),
        lambda l: translate(l, config.translation[0], config.translation[1])
    ]

    sym_funcs = []
    if config.symmetry_x: sym_funcs.append(reflect_x)
    if config.symmetry_y: sym_funcs.append(reflect_y)
    if config.radial_symmetry > 1: sym_funcs.append(radial_symmetry(config.radial_symmetry))

    batch_fn = _get_batch_fn(config.fractal_type)
    
    # Считаем общее число батчей
    all_batches_list = list(batch_fn(config))
    total_batches = len(all_batches_list)

    mode = 'accumulate' if config.fractal_type in _ACCUMULATE else 'replace'

    for batch_idx, raw_lines in enumerate(all_batches_list):
        transformed = apply_to_lines(raw_lines, *transforms)
        
        colored = colorize_lines(transformed, config.color_mode, config.seed)
        
        yield colored, batch_idx, total_batches, mode
