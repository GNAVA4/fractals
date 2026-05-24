"""
Раскраска линий через цветовые палитры.

Цвет линии = семплирование палитры по её относительному индексу t ∈ [0,1].
Индексное (а не length-based) семплирование работает универсально, в том
числе для регулярных фракталов с одинаковой длиной отрезков
(Серпинский, Кох) — где старая length-формула вырождалась в один цвет.

Палитры — хендкрафтнутые стопы в RGB, интерполяция кусочно-линейная.
"""
from dataclasses import dataclass
from .types import Line

RGB = tuple[int, int, int]

# Палитры: упорядоченные RGB-стопы. Подобраны так, чтобы быть читаемыми
# на тёмном фоне (нет совсем тёмных стопов) и иметь luminance-вариацию.
PALETTES: dict[str, list[RGB]] = {
    # Холодная: глубокий синий → бирюза → лёд
    "ocean":   [(40, 70, 160), (60, 140, 220), (90, 220, 235), (220, 250, 250)],
    # Тёплая: бордо → оранжевый → жёлтый
    "fire":    [(120, 25, 60), (220, 60, 50), (255, 145, 50), (255, 230, 130)],
    # Природная: тёмно-зелёный → лайм → пастель
    "forest":  [(30, 110, 70), (90, 200, 100), (190, 230, 110), (240, 250, 200)],
    # Психоделика: индиго → магента → розовый
    "cosmic":  [(70, 20, 130), (160, 60, 220), (235, 110, 235), (250, 210, 250)],
    # Северное сияние: изумруд → циан → лаванда
    "aurora":  [(40, 200, 140), (70, 190, 235), (160, 140, 245), (225, 195, 250)],
    # Закат: пурпур → коралл → жёлтый
    "sunset":  [(90, 35, 130), (220, 75, 130), (255, 145, 85), (255, 225, 135)],
    # Неон: циан → фуксия
    "neon":    [(50, 230, 245), (150, 90, 245), (245, 90, 210), (255, 230, 230)],
    # Монохром: бледно-голубой → белый
    "mono":    [(170, 195, 235), (245, 250, 255)],
}

# Старые имена цветовых режимов мапятся на палитры (back-compat)
_ALIASES = {"gradient": "ocean", "pos": "cosmic"}


@dataclass(frozen=True, slots=True)
class ColorParams:
    """Параметры согласованности цветов между батчами анимации."""
    total: int = 1
    index_offset: int = 0
    seed: int = 42


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def _sample_palette(stops: list[RGB], t: float) -> RGB:
    """Линейная интерполяция между стопами палитры. t ∈ [0,1]."""
    if t <= 0.0:
        return stops[0]
    if t >= 1.0 or len(stops) == 1:
        return stops[-1]
    seg = len(stops) - 1
    pos = t * seg
    i = int(pos)
    frac = pos - i
    a, b = stops[i], stops[i + 1]
    return (
        int(a[0] + (b[0] - a[0]) * frac),
        int(a[1] + (b[1] - a[1]) * frac),
        int(a[2] + (b[2] - a[2]) * frac),
    )


def _hsl_to_rgb(h: float, s: float, l: float) -> RGB:
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60:    r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)


def _resolve_mode(mode: str) -> str:
    return _ALIASES.get(mode, mode)


def compute_color_params(lines: list[Line], _mode: str, seed: int = 42) -> ColorParams:
    """Для индексного семплирования нужен только total. Считается до батчинга."""
    return ColorParams(total=max(1, len(lines)), index_offset=0, seed=seed)


def colorize_lines(
    lines: list[Line],
    mode: str,
    seed: int = 42,
    params: ColorParams | None = None,
) -> list[tuple[Line, str]]:
    """
    Раскрашивает линии. Если params=None — total берётся из текущего батча
    (одиночный рендер). Для согласованности между батчами передавайте
    `ColorParams(total=N_total, index_offset=...)`.
    """
    if not lines:
        return []
    mode = _resolve_mode(mode)

    if params is None:
        total = len(lines)
        offset = 0
    else:
        total = params.total
        offset = params.index_offset

    denom = max(1, total - 1)

    if mode == "rainbow":
        # Полный HSL-спектр с поворотом hue по seed
        hue_shift = (seed * 17) % 360
        return [
            (line, _rgb_to_hex(*_hsl_to_rgb(((i + offset) / denom * 320.0 + hue_shift) % 360, 0.85, 0.6)))
            for i, line in enumerate(lines)
        ]

    palette = PALETTES.get(mode, PALETTES["ocean"])
    return [
        (line, _rgb_to_hex(*_sample_palette(palette, (i + offset) / denom)))
        for i, line in enumerate(lines)
    ]


def palette_preview_stops(mode: str) -> list[RGB]:
    """Вернуть набор RGB-стопов для отрисовки превью в UI."""
    mode = _resolve_mode(mode)
    if mode == "rainbow":
        # 7 стопов по спектру для превью
        return [_hsl_to_rgb(i * 50, 0.85, 0.6) for i in range(7)]
    return PALETTES.get(mode, PALETTES["ocean"])
