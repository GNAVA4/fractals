"""
Панель управления параметрами фрактала.

UX-фичи:
- Селектор типа фрактала — крупные «таблетки» с иконками вместо комбобокса
- Контекстная видимость параметров (например, "угол ветвления" виден только для дерева,
  seed/roughness — только для молнии)
- Сворачиваемые секции
- Чистая работа сигналов (включая QDoubleSpinBox, который раньше не подключался)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QPushButton, QButtonGroup,
    QScrollArea, QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QSize
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QLinearGradient, QRadialGradient, QBrush,
)
from src.core.types import FractalConfig
from src.core.coloring import palette_preview_stops


# ───────────── Палитра ─────────────
ACCENT_BLUE = QColor(74, 143, 231)
ACCENT_PURPLE = QColor(120, 96, 235)
ACCENT_PINK = QColor(232, 90, 158)
ACCENT_RED = QColor(232, 90, 58)
ACCENT_TEAL = QColor(74, 215, 200)
TEXT_PRIMARY = "#dde7f5"
TEXT_SECONDARY = "#9bb0d0"
TEXT_MUTED = "#7088a8"


# ───────────── Базовая стеклянная панель ─────────────
class GlassPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Основной градиент
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(28, 38, 72, 200))
        gradient.setColorAt(0.5, QColor(22, 30, 58, 210))
        gradient.setColorAt(1.0, QColor(14, 20, 44, 220))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(self.rect(), 14, 14)

        # Верхний блик
        highlight = QLinearGradient(0, 0, 0, max(1, int(self.height() * 0.35)))
        highlight.setColorAt(0.0, QColor(255, 255, 255, 28))
        highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(highlight))
        painter.drawRoundedRect(
            self.rect().adjusted(1, 1, -1, -int(self.height() * 0.62)), 14, 14
        )

        # Рамка
        pen = QPen(QColor(90, 140, 230, 90))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 14, 14)


# ───────────── Стеклянная кнопка ─────────────
class GlassButton(QPushButton):
    def __init__(self, text, gradient_colors=None, parent=None):
        super().__init__(text, parent)
        self._default_colors = gradient_colors or [ACCENT_BLUE, ACCENT_PURPLE]
        self._hovered = False
        self._pressed = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setFlat(True)
        self.setStyleSheet("QPushButton { background: transparent; border: none; color: transparent; }")

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        if self.isChecked():
            c1, c2 = ACCENT_RED, ACCENT_PINK
        elif self._pressed:
            c1 = self._default_colors[0].lighter(120)
            c2 = self._default_colors[1].lighter(120)
        elif self._hovered:
            c1 = self._default_colors[0].lighter(110)
            c2 = self._default_colors[1].lighter(110)
        else:
            c1, c2 = self._default_colors

        # Тень
        if self._hovered or self._pressed:
            shadow_pen = QPen(QColor(c1.red(), c1.green(), c1.blue(), 80))
            shadow_pen.setWidthF(6)
            painter.setPen(shadow_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 9, 9)

        # Основной градиент
        grad = QLinearGradient(0, 0, w, 0)
        grad.setColorAt(0.0, c1)
        grad.setColorAt(1.0, c2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(self.rect(), 9, 9)

        # Блик
        highlight = QLinearGradient(0, 0, 0, h * 0.55)
        highlight.setColorAt(0.0, QColor(255, 255, 255, 50))
        highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(highlight))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -int(h * 0.45)), 9, 9)

        # Текст
        text_color = QColor(255, 255, 255, 250)
        font = painter.font()
        font.setBold(True)
        font.setPointSizeF(10.5)
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


# ───────────── Иконочная кнопка типа фрактала ─────────────
class FractalTypeButton(QPushButton):
    """Тоггл-кнопка типа фрактала с иконкой и подписью."""

    FRACTAL_LABELS = {
        "sierpinski": ("△", "Серпинский"),
        "t_fractal":  ("┬", "T-фрактал"),
        "h_fractal":  ("H", "H-фрактал"),
        "koch":       ("❅", "Кох"),
        "tree":       ("🌿", "Дерево"),
        "lightning":  ("⚡", "Молния"),
    }

    def __init__(self, fractal_type: str, parent=None):
        super().__init__(parent)
        self.fractal_type = fractal_type
        self.icon_char, self.label = self.FRACTAL_LABELS[fractal_type]
        self._hovered = False
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(QSize(96, 64))
        self.setFlat(True)
        self.setStyleSheet("QPushButton { background: transparent; border: none; color: transparent; }")

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)

        if self.isChecked():
            grad = QLinearGradient(0, 0, r.width(), r.height())
            grad.setColorAt(0.0, ACCENT_BLUE)
            grad.setColorAt(1.0, ACCENT_PURPLE)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(r, 10, 10)
            # Glow border
            pen = QPen(QColor(160, 200, 255, 180))
            pen.setWidthF(1.5)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(r, 10, 10)
            icon_color = QColor(255, 255, 255, 250)
            text_color = QColor(245, 250, 255, 240)
        else:
            bg = QColor(30, 40, 68, 160) if not self._hovered else QColor(45, 60, 100, 200)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(bg))
            painter.drawRoundedRect(r, 10, 10)
            pen = QPen(QColor(80, 120, 200, 90 if not self._hovered else 160))
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(r, 10, 10)
            icon_color = QColor(180, 210, 250, 230)
            text_color = QColor(170, 195, 230, 220)

        # Иконка
        font = painter.font()
        font.setPointSizeF(20)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(icon_color)
        icon_rect = self.rect().adjusted(0, 4, 0, -22)
        painter.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, self.icon_char)

        # Подпись
        font.setPointSizeF(8.5)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(text_color)
        text_rect = self.rect().adjusted(0, 32, 0, -4)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.label)


# ───────────── Свотч палитры ─────────────
class PaletteSwatch(QPushButton):
    """Кнопка-превью палитры: рисует её градиент, светится при выборе."""

    LABELS = {
        "ocean": "Океан", "fire": "Огонь", "forest": "Лес", "cosmic": "Космос",
        "aurora": "Сияние", "sunset": "Закат", "neon": "Неон", "mono": "Моно",
        "rainbow": "Радуга",
    }

    def __init__(self, palette_name: str, parent=None):
        super().__init__(parent)
        self.palette_name = palette_name
        self.stops = palette_preview_stops(palette_name)
        self._hovered = False
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(QSize(52, 42))
        self.setFlat(True)
        self.setToolTip(self.LABELS.get(palette_name, palette_name.title()))
        self.setStyleSheet("QPushButton { background: transparent; border: none; color: transparent; }")

    def enterEvent(self, event):
        self._hovered = True; self.update(); super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False; self.update(); super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(2, 2, -2, -2)

        # Свечение для выбранной
        if self.isChecked():
            glow = QRadialGradient(r.center().x(), r.center().y(), r.width())
            mid = self.stops[len(self.stops) // 2]
            glow.setColorAt(0.0, QColor(mid[0], mid[1], mid[2], 150))
            glow.setColorAt(1.0, QColor(mid[0], mid[1], mid[2], 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawRoundedRect(self.rect(), 8, 8)

        # Сам градиент палитры
        grad = QLinearGradient(r.left(), 0, r.right(), 0)
        n = len(self.stops)
        for i, (red, green, blue) in enumerate(self.stops):
            grad.setColorAt(i / max(1, n - 1), QColor(red, green, blue))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(r, 7, 7)

        # Рамка
        if self.isChecked():
            pen = QPen(QColor(255, 255, 255, 230))
            pen.setWidthF(2.0)
        elif self._hovered:
            pen = QPen(QColor(220, 235, 255, 200))
            pen.setWidthF(1.3)
        else:
            pen = QPen(QColor(90, 130, 200, 110))
            pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(r, 7, 7)


# ───────────── Слайдер ─────────────
class GlassSlider(QWidget):
    value_changed = pyqtSignal(int)

    def __init__(self, min_val, max_val, default, parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.current_value = default
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(120)

    def _x_to_value(self, x: int) -> int:
        w = max(1, self.width() - 20)
        ratio = max(0.0, min(1.0, (x - 10) / w))
        return int(round(self.min_val + ratio * (self.max_val - self.min_val)))

    def _value_to_x(self, value: int) -> int:
        if self.max_val == self.min_val:
            return 10
        ratio = (value - self.min_val) / (self.max_val - self.min_val)
        return int(10 + ratio * (self.width() - 20))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._set_value(self._x_to_value(int(event.position().x())))

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._set_value(self._x_to_value(int(event.position().x())))

    def _set_value(self, value: int):
        value = max(self.min_val, min(value, self.max_val))
        if value != self.current_value:
            self.current_value = value
            self.update()
            self.value_changed.emit(value)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        track_y = h // 2 - 3

        # Track фон
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(20, 30, 55, 200)))
        painter.drawRoundedRect(10, track_y, w - 20, 6, 3, 3)

        # Track заливка
        handle_x = self._value_to_x(self.current_value)
        if handle_x > 10:
            grad = QLinearGradient(10, 0, handle_x, 0)
            grad.setColorAt(0.0, ACCENT_BLUE)
            grad.setColorAt(1.0, ACCENT_PURPLE)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(10, track_y, handle_x - 10, 6, 3, 3)

        # Handle
        handle_r = 9
        # Glow
        glow = QRadialGradient(handle_x, h // 2, handle_r * 2)
        glow.setColorAt(0.0, QColor(120, 160, 240, 130))
        glow.setColorAt(1.0, QColor(120, 160, 240, 0))
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QPoint(handle_x, h // 2), handle_r * 2, handle_r * 2)
        # Тело
        painter.setBrush(QBrush(QColor(245, 250, 255, 255)))
        painter.drawEllipse(QPoint(handle_x, h // 2), handle_r, handle_r)
        # Внутренняя точка
        painter.setBrush(QBrush(ACCENT_PURPLE))
        painter.drawEllipse(QPoint(handle_x, h // 2), 3, 3)


# ───────────── Кастомный чекбокс ─────────────
class GlassCheckBox(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._checked = False
        self._hovered = False
        self.text = text
        self.setMinimumHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self.update()
            self.toggled.emit(self._checked)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, v: bool):
        if self._checked != v:
            self._checked = v
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        y = (self.height() - 18) // 2
        x = 2

        if self._checked:
            grad = QLinearGradient(x, y, x + 18, y + 18)
            grad.setColorAt(0.0, ACCENT_BLUE)
            grad.setColorAt(1.0, ACCENT_PURPLE)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(x, y, 18, 18, 5, 5)
            # Галка
            pen = QPen(QColor(255, 255, 255, 250))
            pen.setWidthF(2.4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawPolyline(*[
                QPoint(x + 4, y + 9),
                QPoint(x + 8, y + 13),
                QPoint(x + 14, y + 5),
            ])
        else:
            border = QColor(120, 160, 220, 200 if self._hovered else 110)
            painter.setPen(QPen(border, 1.4))
            painter.setBrush(QBrush(QColor(20, 30, 55, 100)))
            painter.drawRoundedRect(x, y, 18, 18, 5, 5)

        # Текст
        text_rect = self.rect().adjusted(28, 0, 0, 0)
        painter.setPen(QColor(TEXT_SECONDARY))
        font = painter.font()
        font.setPointSizeF(10)
        painter.setFont(font)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text)


# ───────────── Числовой инпут ─────────────
class GlassSpinbox(QWidget):
    """Обёртка над QSpinBox/QDoubleSpinBox с +/- кнопками. valueChanged проксируется."""
    valueChanged = pyqtSignal(float)

    def __init__(self, min_val, max_val, default, step=1, decimals=0, parent=None):
        super().__init__(parent)
        self.is_double = decimals > 0 or isinstance(step, float)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self.spin = QDoubleSpinBox() if self.is_double else QSpinBox()
        if self.is_double:
            self.spin.setDecimals(decimals or 2)
        self.spin.setRange(min_val, max_val)
        self.spin.setValue(default)
        self.spin.setSingleStep(step)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin.setStyleSheet("""
            QSpinBox, QDoubleSpinBox {
                background: rgba(15, 22, 44, 220);
                border: 1px solid rgba(90, 140, 220, 90);
                border-radius: 7px;
                color: #dde7f5;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 6px;
                min-height: 22px;
                selection-background-color: rgba(74, 143, 231, 150);
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid rgba(120, 180, 240, 200);
            }
        """)

        self.down_btn = self._mini_btn("−")
        self.up_btn = self._mini_btn("+")
        self.down_btn.clicked.connect(self.spin.stepDown)
        self.up_btn.clicked.connect(self.spin.stepUp)

        layout.addWidget(self.down_btn)
        layout.addWidget(self.spin, 1)
        layout.addWidget(self.up_btn)

        self.spin.valueChanged.connect(lambda v: self.valueChanged.emit(float(v)))

    def _mini_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(22, 22)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(60, 100, 180, 200), stop:1 rgba(40, 70, 140, 200));
                color: #f0f6ff;
                border: 1px solid rgba(120, 170, 230, 100);
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(90, 140, 220, 220), stop:1 rgba(70, 100, 180, 220));
            }
            QPushButton:pressed {
                background: rgba(50, 80, 160, 220);
            }
        """)
        return btn

    def value(self):
        return self.spin.value()


# ───────────── Лейблированный ряд ─────────────
def _labeled_row(label_text: str, widget: QWidget) -> QWidget:
    """Стандартный ряд: подпись + виджет."""
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 3, 0, 3)
    layout.setSpacing(10)
    lbl = QLabel(label_text)
    lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
    lbl.setMinimumWidth(110)
    layout.addWidget(lbl)
    layout.addWidget(widget, 1)
    return row


# ───────────── Заголовок секции ─────────────
def _section_header(text: str, color: str = "#7fb3ff") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        color: {color};
        font-size: 11px;
        font-weight: bold;
        padding: 6px 0 2px 0;
        letter-spacing: 1px;
    """)
    return lbl


# ───────────── Главная панель ─────────────
class ControlsPanel(QWidget):
    parameters_changed = pyqtSignal()

    # Какие параметры активны для каждого типа фрактала
    PARAM_VISIBILITY = {
        "sierpinski": {"scale": False, "tree_spread": False, "lightning": False},
        "t_fractal":  {"scale": True,  "tree_spread": False, "lightning": False},
        "h_fractal":  {"scale": True,  "tree_spread": False, "lightning": False},
        "koch":       {"scale": False, "tree_spread": False, "lightning": False},
        "tree":       {"scale": True,  "tree_spread": True,  "lightning": False},
        "lightning":  {"scale": False, "tree_spread": False, "lightning": True},
    }

    def __init__(self):
        super().__init__()
        self._build_ui()
        self._connect_signals()
        self._update_visibility("sierpinski")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(14, 20, 40, 240))
        gradient.setColorAt(0.5, QColor(18, 26, 50, 245))
        gradient.setColorAt(1.0, QColor(12, 17, 35, 248))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(self.rect(), 18, 18)
        # Тонкая рамка
        pen = QPen(QColor(80, 130, 220, 100))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 18, 18)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(0)

        # Заголовок
        title = QLabel("✦  Фракталы")
        title.setStyleSheet(f"""
            color: {TEXT_PRIMARY};
            font-size: 19px;
            font-weight: bold;
            padding: 2px 0 12px 4px;
            letter-spacing: 1px;
        """)
        outer.addWidget(title)

        # ─── Прокручиваемый контейнер ───
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: rgba(20, 30, 55, 120); width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(90, 140, 220, 160); border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: rgba(120, 170, 240, 220); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(8)

        # ─── Тип фрактала: сетка кнопок ───
        layout.addWidget(_section_header("ТИП ФРАКТАЛА"))
        types_grid = self._build_fractal_grid()
        layout.addWidget(types_grid)

        # ─── Общие параметры ───
        common_panel = GlassPanel()
        common_layout = QVBoxLayout(common_panel)
        common_layout.setContentsMargins(14, 12, 14, 12)
        common_layout.setSpacing(6)
        common_layout.addWidget(_section_header("ГЕОМЕТРИЯ", "#8fc4ff"))

        self.depth_spin = GlassSpinbox(1, 12, 4, step=1)
        common_layout.addWidget(_labeled_row("Глубина", self.depth_spin))

        self.scale_spin = GlassSpinbox(0.1, 0.9, 0.5, step=0.05, decimals=2)
        self.scale_row = _labeled_row("Масштаб реc.", self.scale_spin)
        common_layout.addWidget(self.scale_row)

        self.tree_spread_spin = GlassSpinbox(5.0, 60.0, 25.0, step=1.0, decimals=1)
        self.tree_spread_row = _labeled_row("Угол ветвей", self.tree_spread_spin)
        common_layout.addWidget(self.tree_spread_row)

        self.display_spin = GlassSpinbox(50.0, 800.0, 300.0, step=10.0, decimals=0)
        common_layout.addWidget(_labeled_row("Размер", self.display_spin))

        self.rot_spin = GlassSpinbox(-360.0, 360.0, 0.0, step=5.0, decimals=1)
        common_layout.addWidget(_labeled_row("Поворот °", self.rot_spin))

        self.width_spin = GlassSpinbox(0.5, 5.0, 1.5, step=0.25, decimals=2)
        common_layout.addWidget(_labeled_row("Толщина", self.width_spin))

        layout.addWidget(common_panel)

        # ─── Параметры молнии ───
        self.lightning_panel = GlassPanel()
        lightning_layout = QVBoxLayout(self.lightning_panel)
        lightning_layout.setContentsMargins(14, 12, 14, 12)
        lightning_layout.setSpacing(6)
        lightning_layout.addWidget(_section_header("⚡ МОЛНИЯ", "#ffd166"))

        self.seed_spin = GlassSpinbox(0, 9999, 42, step=1)
        lightning_layout.addWidget(_labeled_row("Seed", self.seed_spin))

        self.rough_spin = GlassSpinbox(0.0, 1.5, 0.8, step=0.05, decimals=2)
        lightning_layout.addWidget(_labeled_row("Шероховатость", self.rough_spin))

        layout.addWidget(self.lightning_panel)

        # ─── Палитра ───
        color_panel = GlassPanel()
        color_layout = QVBoxLayout(color_panel)
        color_layout.setContentsMargins(14, 12, 14, 12)
        color_layout.setSpacing(8)
        color_layout.addWidget(_section_header("ПАЛИТРА", "#d18fff"))

        self.color_buttons = QButtonGroup(self)
        self.color_buttons.setExclusive(True)
        self._palette_label = QLabel("Сияние")
        self._palette_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px; font-weight: bold;")
        self._palette_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Палитры: 5 в первом ряду + 4 во втором (включая радугу)
        palette_names = ["ocean", "aurora", "cosmic", "sunset", "fire",
                         "forest", "neon", "rainbow", "mono"]
        default = "aurora"

        for row_palettes in (palette_names[:5], palette_names[5:]):
            row = QHBoxLayout()
            row.setSpacing(5)
            row.setContentsMargins(0, 0, 0, 0)
            for name in row_palettes:
                sw = PaletteSwatch(name)
                if name == default:
                    sw.setChecked(True)
                self.color_buttons.addButton(sw)
                row.addWidget(sw)
            row.addStretch()
            rw = QWidget()
            rw.setLayout(row)
            color_layout.addWidget(rw)

        color_layout.addWidget(self._palette_label)
        layout.addWidget(color_panel)

        # ─── Симметрия ───
        sym_panel = GlassPanel()
        sym_layout = QVBoxLayout(sym_panel)
        sym_layout.setContentsMargins(14, 12, 14, 12)
        sym_layout.setSpacing(6)
        sym_layout.addWidget(_section_header("СИММЕТРИЯ", "#4ad7c8"))

        self.sym_x_check = GlassCheckBox("Отражение по X")
        self.sym_y_check = GlassCheckBox("Отражение по Y")
        sym_layout.addWidget(self.sym_x_check)
        sym_layout.addWidget(self.sym_y_check)

        self.radial_spin = GlassSpinbox(0, 12, 0, step=1)
        sym_layout.addWidget(_labeled_row("Радиальная N", self.radial_spin))

        layout.addWidget(sym_panel)

        # ─── Анимация ───
        anim_panel = GlassPanel()
        anim_layout = QVBoxLayout(anim_panel)
        anim_layout.setContentsMargins(14, 12, 14, 12)
        anim_layout.setSpacing(6)
        anim_layout.addWidget(_section_header("АНИМАЦИЯ", "#ff8fa3"))

        speed_row = QHBoxLayout()
        speed_row.setSpacing(8)
        speed_lbl = QLabel("Скорость")
        speed_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self.speed_label_widget = QLabel("15 л/с")
        self.speed_label_widget.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px; font-weight: bold;")
        self.speed_label_widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        speed_row.addWidget(speed_lbl)
        speed_row.addWidget(self.speed_label_widget, 1)
        sw = QWidget()
        sw.setLayout(speed_row)
        anim_layout.addWidget(sw)

        self.speed_slider = GlassSlider(1, 50, 15)
        anim_layout.addWidget(self.speed_slider)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.play_btn = GlassButton("▶  Запуск", [ACCENT_BLUE, ACCENT_PURPLE])
        self.play_btn.setCheckable(True)
        self.reset_btn = GlassButton("↺  Сброс", [QColor(60, 80, 130), QColor(40, 55, 95)])
        btn_row.addWidget(self.play_btn, 2)
        btn_row.addWidget(self.reset_btn, 1)
        bw = QWidget()
        bw.setLayout(btn_row)
        anim_layout.addWidget(bw)

        layout.addWidget(anim_panel)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _build_fractal_grid(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 4, 0, 8)
        layout.setSpacing(6)

        self.fractal_buttons = QButtonGroup(self)
        self.fractal_buttons.setExclusive(True)

        types = ["sierpinski", "t_fractal", "h_fractal", "koch", "tree", "lightning"]
        # 2 ряда по 3
        for i in range(0, len(types), 3):
            row = QHBoxLayout()
            row.setSpacing(6)
            for t in types[i:i + 3]:
                btn = FractalTypeButton(t)
                if t == "sierpinski":
                    btn.setChecked(True)
                self.fractal_buttons.addButton(btn)
                row.addWidget(btn)
            rw = QWidget()
            rw.setLayout(row)
            layout.addWidget(rw)
        return wrapper

    # ───────── Сигналы ─────────
    def _connect_signals(self):
        # Тип фрактала
        self.fractal_buttons.buttonClicked.connect(self._on_fractal_changed)
        # Палитра
        self.color_buttons.buttonClicked.connect(self._on_palette_changed)
        # Числовые поля (GlassSpinbox имеет собственный valueChanged)
        for spin in (
            self.depth_spin, self.scale_spin, self.tree_spread_spin,
            self.display_spin, self.rot_spin, self.width_spin,
            self.seed_spin, self.rough_spin, self.radial_spin,
        ):
            spin.valueChanged.connect(lambda *_: self.parameters_changed.emit())
        # Чекбоксы
        self.sym_x_check.toggled.connect(lambda _v: self.parameters_changed.emit())
        self.sym_y_check.toggled.connect(lambda _v: self.parameters_changed.emit())
        # Скорость
        self.speed_slider.value_changed.connect(self._on_speed_change)

    def _on_fractal_changed(self, btn: FractalTypeButton):
        self._update_visibility(btn.fractal_type)
        self.parameters_changed.emit()

    def _update_visibility(self, fractal_type: str):
        vis = self.PARAM_VISIBILITY.get(fractal_type, {})
        self.scale_row.setVisible(vis.get("scale", False))
        self.tree_spread_row.setVisible(vis.get("tree_spread", False))
        self.lightning_panel.setVisible(vis.get("lightning", False))

    def _on_speed_change(self, value: int):
        self.speed_label_widget.setText(f"{value} л/с")

    def _on_palette_changed(self, btn: "PaletteSwatch"):
        self._palette_label.setText(PaletteSwatch.LABELS.get(btn.palette_name, btn.palette_name))
        self.parameters_changed.emit()

    # ───────── Публичный API ─────────
    def get_config(self) -> FractalConfig:
        # Активный тип
        ftype = "sierpinski"
        for btn in self.fractal_buttons.buttons():
            if btn.isChecked():
                ftype = btn.fractal_type
                break
        # Активная палитра
        cmode = "aurora"
        for btn in self.color_buttons.buttons():
            if btn.isChecked():
                cmode = btn.palette_name
                break

        return FractalConfig(
            fractal_type=ftype,
            depth=int(self.depth_spin.value()),
            scale=float(self.scale_spin.value()),
            display_scale=float(self.display_spin.value()),
            rotation_deg=float(self.rot_spin.value()),
            line_width=float(self.width_spin.value()),
            color_mode=cmode,
            tree_spread=float(self.tree_spread_spin.value()),
            symmetry_x=self.sym_x_check.isChecked(),
            symmetry_y=self.sym_y_check.isChecked(),
            radial_symmetry=int(self.radial_spin.value()),
            seed=int(self.seed_spin.value()),
            roughness=float(self.rough_spin.value()),
        )

    def get_animation_speed(self) -> int:
        return self.speed_slider.current_value

    def is_animation_playing(self) -> bool:
        return self.play_btn.isChecked()
