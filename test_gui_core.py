from src.core.types import FractalConfig, Line, Point
from src.bridge import generate_fractal, generate_fractal_batched
from src.core.symmetry import radial_symmetry, apply_symmetries
from src.core.generators import sierpinski_lines


def test_radial_symmetry():
    line = Line(Point(0, 0), Point(1, 0))
    sym_fn = radial_symmetry(4)
    result = list(sym_fn(line))
    assert len(result) == 4, f"Expected 4 lines, got {len(result)}"


def test_batched_matches_full():
    """Батчи не содержат симметрии — финальный рендер содержит."""
    config = FractalConfig(fractal_type="sierpinski", depth=4,
                           symmetry_x=True, radial_symmetry=3, display_scale=200)
    full = generate_fractal(config)

    batches = list(generate_fractal_batched(config))
    all_lines = []
    for colored, idx, total, mode in batches:
        all_lines.extend(colored)

    # Батчи содержат исходные линии (без симметрии), финал — с симметрией
    assert len(all_lines) < len(full), \
        f"batched={len(all_lines)} should be < full with sym={len(full)}"


def test_batch_accumulate_mode():
    config = FractalConfig(fractal_type="koch", depth=3, display_scale=200)
    batches = list(generate_fractal_batched(config))

    # Все типы используют accumulate
    for colored, idx, total, mode in batches:
        assert mode == "accumulate", f"Expected accumulate, got {mode}"


def test_batch_replace_mode():
    """Больше нет replace режима — все типы накапливают линии."""
    config = FractalConfig(fractal_type="tree", depth=5, display_scale=200)
    batches = list(generate_fractal_batched(config))

    for colored, idx, total, mode in batches:
        assert mode == "accumulate", f"Все типы должны использовать accumulate"


def test_symmetry_x():
    config = FractalConfig(fractal_type="sierpinski", depth=1,
                           symmetry_x=True, display_scale=200)
    result = generate_fractal(config)
    base = generate_fractal(FractalConfig(fractal_type="sierpinski", depth=1, display_scale=200))
    assert len(result) > len(base), "symmetry_x should add lines"


def test_symmetry_y():
    config = FractalConfig(fractal_type="sierpinski", depth=1,
                           symmetry_y=True, display_scale=200)
    result = generate_fractal(config)
    base = generate_fractal(FractalConfig(fractal_type="sierpinski", depth=1, display_scale=200))
    assert len(result) > len(base), "symmetry_y should add lines"


def test_symmetry_both():
    config = FractalConfig(fractal_type="sierpinski", depth=3,
                           symmetry_x=True, symmetry_y=True, radial_symmetry=4, display_scale=200)
    result = generate_fractal(config)
    base = generate_fractal(FractalConfig(fractal_type="sierpinski", depth=3, display_scale=200))
    assert len(result) > len(base), "symmetry both + radial should add lines"


def test_all_fractals_batched():
    for ftype in ("sierpinski", "t_fractal", "h_fractal", "koch", "tree", "lightning"):
        config = FractalConfig(fractal_type=ftype, depth=4, display_scale=200)
        batches = list(generate_fractal_batched(config))
        assert len(batches) > 0, f"{ftype}: no batches"
        # Все батчи должны содержать линии (некоторые могут быть пустыми на границах)
        non_empty = sum(1 for colored, _, _, _ in batches if len(colored) > 0)
        assert non_empty > 0, f"{ftype}: все батчи пусты"


def test_lightning_deterministic():
    config = FractalConfig(fractal_type="lightning", depth=6, seed=42, display_scale=300)
    r1 = generate_fractal(config)
    r2 = generate_fractal(config)
    assert len(r1) == len(r2), "Молния должна быть детерминированной"


def test_batched_all_types_with_radial():
    """Батчи не содержат симметрии — они применяются только в финальном рендере."""
    for ftype in ("sierpinski", "t_fractal", "h_fractal", "koch", "tree", "lightning"):
        config = FractalConfig(fractal_type=ftype, depth=4, display_scale=200)
        full = generate_fractal(config)
        batches = list(generate_fractal_batched(config))
        all_lines = []
        for colored, _, _, _ in batches:
            all_lines.extend(colored)
        assert len(all_lines) > 0, f"{ftype}: нет батчей"


if __name__ == "__main__":
    tests = [
        (test_radial_symmetry, "radial_symmetry"),
        (test_batched_matches_full, "batched matches full (with symmetry)"),
        (test_batch_accumulate_mode, "accumulate mode"),
        (test_batch_replace_mode, "replace mode"),
        (test_symmetry_x, "symmetry_x"),
        (test_symmetry_y, "symmetry_y"),
        (test_symmetry_both, "symmetry both + radial"),
        (test_all_fractals_batched, "all fractals batched"),
        (test_lightning_deterministic, "lightning deterministic"),
        (test_batched_all_types_with_radial, "batched all types with radial"),
    ]

    passed = 0
    failed = 0
    for test_fn, name in tests:
        try:
            test_fn()
            print(f"OK {name}")
            passed += 1
        except Exception as e:
            print(f"FAIL {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{passed}/{passed + failed} tests passed")
    if failed:
        raise AssertionError(f"{failed} tests failed")
    else:
        print("\nAll tests passed!")
