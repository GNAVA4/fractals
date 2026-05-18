import math
from .types import Line

def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"

def _hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60: r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else: r, g, b = c, 0, x
    return int((r+m)*255), int((g+m)*255), int((b+m)*255)

def colorize_lines(lines: list[Line], mode: str, seed: int = 42) -> list[tuple[Line, str]]:
    if not lines:
        return []
    
    if mode == "rainbow":
        return [(line, _rgb_to_hex(*_hsl_to_rgb((i * 37 + seed*13) % 360, 0.9, 0.6))) 
                for i, line in enumerate(lines)]
    elif mode == "gradient":
        lengths = [math.hypot(line.end.x - line.start.x, line.end.y - line.start.y) for line in lines]
        max_len = max(lengths) if lengths else 1.0
        return [(line, _rgb_to_hex(*_hsl_to_rgb(200 + (ln / max_len) * 160, 0.85, 0.5)))
                for line, ln in zip(lines, lengths)]
    elif mode == "pos":
        cx = sum((line.start.x + line.end.x) / 2 for line in lines) / len(lines)
        return [(line, _rgb_to_hex(*_hsl_to_rgb(abs(((line.start.x + line.end.x) / 2 - cx) * 100 + seed) % 360, 0.8, 0.55)))
                for line in lines]
    return [(line, "#333333") for line in lines]