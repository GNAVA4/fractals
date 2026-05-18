# Фракталы — Liquid Glass

PyQt6 десктопное приложение для визуализации фракталов с анимацией и стеклянным UI.

## Возможности

- **6 типов фракталов**: Серпинский, T-фрактал, H-фрактал, Кох, Дерево, Молния
- **Анимация** — плавная генерация линий по батчам с прогресс-баром
- **Раскраска**: gradient (по длине), rainbow (спектр), pos (по позиции)
- **Симметрия**: отражение по X/Y + n-кратная радиальная симметрия
- **Параметры**: глубина, масштаб рекурсии, масштаб отображения, поворот, толщина линий, угол ветвления
- **Горячие клавиши**: колёсико мыши — зум, перетаскивание — панорама, двойной клик — сброс

## Установка

```bash
cd Graph
python -m venv venv
venv\Scripts\activate
pip install PyQt6
```

## Запуск

```bash
python app.py
```

## Тесты

```bash
python test_gui_core.py   # ядро + bridge
python test_core.py        # базовые тесты моста
```

## Архитектура

```
app.py                    # Точка входа (QApplication → MainWindow)
├── src/core/            # Ядро (чистая логика, без GUI)
│   ├── types.py         # Point, Line, FractalConfig (frozen dataclasses)
│   ├── generators.py    # 6 фракталов + batched-генераторы для анимации
│   ├── lightning.py     # Фрактальная молния (det. noise)
│   ├── coloring.py      # Раскраска HSL→hex (gradient/rainbow/pos)
│   ├── transforms.py    # translate, rotate, scale (чистые функции)
│   ├── symmetry.py      # reflect_x/y, radial_symmetry, композиция
│   └── utils.py         # compose, apply_to_lines, flatten_lines
├── src/bridge.py        # Мост: генерация → трансформации → симметрии → раскраска
└── src/gui/             # GUI (PyQt6)
    ├── main_window.py   # GlassWindow + MainWindow (таймеры, анимация)
    ├── canvas.py        # FractalCanvas (paintEvent: основной слой)
    └── controls.py      # ControlsPanel + кастомные glass-виджеты
```

## License

MIT
