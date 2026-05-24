from src.core.types import FractalConfig, Line, Point
from src.bridge import generate_fractal, generate_fractal_batched
from src.core.symmetry import radial_symmetry, apply_symmetries, reflect_x, reflect_y


def test_radial_symmetry_new_api():
    """radial_symmetry(n) выдаёт n-1 копий (без оригинала). Оригинал добавляет apply_symmetries."""
    line = Line(Point(1.0, 0.0), Point(2.0, 0.0))
    sym_fn = radial_symmetry(4)
    result = list(sym_fn(line))
    assert len(result) == 3, f"Expected 3 new copies (n-1), got {len(result)}"


def test_apply_symmetries_dihedral():
    """reflect_x ∘ reflect_y должны давать 4 линии (D2 группа)."""
    line = Line(Point(1.0, 2.0), Point(3.0, 4.0))
    result = apply_symmetries([line], reflect_x, reflect_y)
    assert len(result) == 4, f"Expected 4 (D2 orbit), got {len(result)}"
    # Проверяем все 4 квадранта
    xs = sorted([(l.start.x, l.start.y) for l in result])
    assert (-3.0, -4.0) in [(l.start.x, l.start.y) for l in result] or \
           (-1.0, -2.0) in [(l.start.x, l.start.y) for l in result]


def test_apply_symmetries_radial_with_reflect():
    """radial(4) ∘ reflect_x должны давать 4 * 2 = 8 линий."""
    line = Line(Point(1.0, 0.0), Point(2.0, 0.0))
    result = apply_symmetries([line], radial_symmetry(4), reflect_x)
    assert len(result) == 8, f"Expected 8 (D4 orbit), got {len(result)}"


def test_no_symmetry_passthrough():
    line = Line(Point(0.0, 0.0), Point(1.0, 1.0))
    result = apply_symmetries([line])
    assert len(result) == 1


def test_symmetry_x_doubles_lines():
    config = FractalConfig(fractal_type="sierpinski", depth=1, display_scale=200)
    base = generate_fractal(config)
    config_x = FractalConfig(fractal_type="sierpinski", depth=1, symmetry_x=True, display_scale=200)
    result = generate_fractal(config_x)
    assert len(result) == 2 * len(base), "symmetry_x должна удваивать число линий"


def test_symmetry_xy_quadruples_lines():
    config = FractalConfig(fractal_type="sierpinski", depth=1, display_scale=200)
    base = generate_fractal(config)
    config_xy = FractalConfig(
        fractal_type="sierpinski", depth=1,
        symmetry_x=True, symmetry_y=True, display_scale=200,
    )
    result = generate_fractal(config_xy)
    assert len(result) == 4 * len(base), \
        f"X+Y должны давать 4x: ожидаем {4*len(base)}, получили {len(result)}"


def test_batch_total_consistent():
    """Сумма линий по батчам = число raw-линий с симметриями."""
    config = FractalConfig(fractal_type="koch", depth=3, display_scale=200, symmetry_x=True)
    batches = list(generate_fractal_batched(config))
    assert len(batches) > 0
    total_lines = sum(len(b) for b, _, _ in batches)
    full = generate_fractal(config)
    assert total_lines == len(full), \
        f"batched({total_lines}) должен равняться full({len(full)})"


def test_batch_signature_three_tuple():
    """generate_fractal_batched теперь возвращает (lines, idx, total) без mode."""
    config = FractalConfig(fractal_type="tree", depth=4, display_scale=200)
    for item in generate_fractal_batched(config):
        assert len(item) == 3, f"Кортеж должен быть из 3-х элементов, получили {len(item)}"
        lines, idx, total = item
        assert isinstance(idx, int) and isinstance(total, int)


def test_all_fractals_batched():
    for ftype in ("sierpinski", "t_fractal", "h_fractal", "koch", "tree", "lightning"):
        config = FractalConfig(fractal_type=ftype, depth=4, display_scale=200)
        batches = list(generate_fractal_batched(config))
        assert len(batches) > 0, f"{ftype}: нет батчей"
        non_empty = sum(1 for colored, _, _ in batches if len(colored) > 0)
        assert non_empty > 0, f"{ftype}: все батчи пусты"


def test_lightning_deterministic():
    config = FractalConfig(fractal_type="lightning", depth=6, seed=42, display_scale=300)
    r1 = generate_fractal(config)
    r2 = generate_fractal(config)
    assert len(r1) == len(r2)
    for (l1, c1), (l2, c2) in zip(r1, r2):
        assert l1.start.x == l2.start.x and l1.start.y == l2.start.y
        assert c1 == c2


def test_lightning_batched_matches_full():
    """Bug-fix #2: батчи молнии должны давать тот же финальный набор линий, что и полная генерация."""
    config = FractalConfig(fractal_type="lightning", depth=6, seed=42,
                           roughness=0.7, display_scale=300)
    full = generate_fractal(config)
    batches = list(generate_fractal_batched(config))
    all_batch_lines = [item for b, _, _ in batches for item in b]
    assert len(all_batch_lines) == len(full), \
        f"Молния: batched={len(all_batch_lines)}, full={len(full)}"


def test_colors_stable_across_batches():
    """Bug-fix #3: цвета в gradient-режиме должны быть согласованы между батчами."""
    config = FractalConfig(fractal_type="tree", depth=5, display_scale=200,
                           color_mode="gradient")
    full = generate_fractal(config)
    batches = list(generate_fractal_batched(config))
    all_batch_colored = [item for b, _, _ in batches for item in b]
    # Цвет конкретной линии в полном рендере должен совпадать с цветом в батч-рендере
    full_map = {(l.start.x, l.start.y, l.end.x, l.end.y): c for l, c in full}
    for line, color in all_batch_colored:
        key = (line.start.x, line.start.y, line.end.x, line.end.y)
        assert full_map.get(key) == color, \
            f"Цвет линии в батче не совпадает с full: {color} vs {full_map.get(key)}"


if __name__ == "__main__":
    tests = [
        test_radial_symmetry_new_api,
        test_apply_symmetries_dihedral,
        test_apply_symmetries_radial_with_reflect,
        test_no_symmetry_passthrough,
        test_symmetry_x_doubles_lines,
        test_symmetry_xy_quadruples_lines,
        test_batch_total_consistent,
        test_batch_signature_three_tuple,
        test_all_fractals_batched,
        test_lightning_deterministic,
        test_lightning_batched_matches_full,
        test_colors_stable_across_batches,
    ]

    passed = failed = 0
    for fn in tests:
        try:
            fn()
            print(f"OK  {fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL {fn.__name__}: {e}")
            import traceback; traceback.print_exc()
            failed += 1

    print(f"\n{passed}/{passed + failed} tests passed")
    if failed:
        raise SystemExit(1)
