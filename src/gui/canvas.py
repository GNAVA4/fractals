"""
Canvas-виджет: рисует линии фрактала с кэшированным фоном и группировкой по цвету.
Оптимизация: фон + сетка переотрисовываются только при resize, не на каждый кадр.
Линии одного цвета рисуются одним `drawLines` вместо create-pen-per-line.
"""
from collections import defaultdict
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QLineF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QLinearGradient, QRadialGradient,
    QBrush, QPixmap,
)


class FractalCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.colored_lines: list = []
        self.line_width: float = 1.5

        # Навигация
        self.zoom: float = 1.0
        self.pan_x: float = 0.0
        self.pan_y: float = 0.0
        self.is_panning: bool = False
        self.last_pos = QPointF()

        # Анимация
        self.anim_lines: list = []
        self._anim_total: int = 0

        # Кэш фона
        self._bg_cache: QPixmap | None = None

        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)

    # ────────── Public API ──────────
    def set_data(self, colored_lines: list, line_width: float):
        self.colored_lines = colored_lines
        self.line_width = line_width
        self.anim_lines = []
        self._anim_total = 0
        self.update()

    def set_anim_state(self, lines: list, total: int):
        self.anim_lines = lines if lines else []
        self._anim_total = total
        self.update()

    # ────────── Resize ──────────
    def resizeEvent(self, event):
        self._bg_cache = None
        super().resizeEvent(event)

    # ────────── Paint ──────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Кэшированный фон + сетка
        if self._bg_cache is None or self._bg_cache.size() != self.size():
            self._rebuild_background()
        painter.drawPixmap(0, 0, self._bg_cache)

        # Координатная трансформация
        cx, cy = self.width() / 2.0, self.height() / 2.0
        painter.save()
        painter.translate(cx + self.pan_x, cy + self.pan_y)
        painter.scale(self.zoom, -self.zoom)

        draw_lines = self.anim_lines if self.anim_lines else self.colored_lines
        if draw_lines:
            self._draw_lines_grouped(painter, draw_lines)

        painter.restore()

        # Прогресс-бар (поверх трансформации)
        if self.anim_lines and self._anim_total > 0:
            self._draw_progress(painter)

    def _draw_lines_grouped(self, painter: QPainter, draw_lines: list):
        """Группирует линии по цвету и рисует одним drawLines на цвет."""
        groups: dict[str, list[QLineF]] = defaultdict(list)
        for line, color_hex in draw_lines:
            groups[color_hex].append(
                QLineF(line.start.x, line.start.y, line.end.x, line.end.y)
            )

        for color_hex, qlines in groups.items():
            color = QColor(color_hex)
            color.setAlpha(240)
            pen = QPen(color)
            pen.setWidthF(self.line_width / max(self.zoom, 0.01))  # масштаб-инвариантная толщина
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLines(qlines)

    def _rebuild_background(self):
        """Перерисовывает фон+сетку в QPixmap (вызывается при resize)."""
        pm = QPixmap(self.size())
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Радиальный градиент-виньетка
        cx, cy = self.width() / 2, self.height() / 2
        radius = max(self.width(), self.height()) * 0.75
        bg = QRadialGradient(cx, cy, radius, cx, cy)
        bg.setColorAt(0.0, QColor(22, 32, 60))
        bg.setColorAt(0.5, QColor(14, 22, 42))
        bg.setColorAt(1.0, QColor(5, 8, 18))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg))
        p.drawRect(self.rect())

        # Сетка
        grid_color = QColor(60, 90, 160, 28)
        pen = QPen(grid_color)
        pen.setWidthF(1)
        p.setPen(pen)
        step = 50
        w, h = self.width(), self.height()
        for x in range(0, w, step):
            p.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            p.drawLine(0, y, w, y)

        # Центральные оси (чуть ярче)
        axis_pen = QPen(QColor(90, 140, 220, 60))
        axis_pen.setWidthF(1.2)
        p.setPen(axis_pen)
        p.drawLine(int(cx), 0, int(cx), h)
        p.drawLine(0, int(cy), w, int(cy))

        # Тонкая внутренняя рамка
        border = QPen(QColor(70, 110, 200, 80))
        border.setWidthF(1.0)
        p.setPen(border)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 14, 14)

        p.end()
        self._bg_cache = pm

    def _draw_progress(self, painter: QPainter):
        bar_w, bar_h = 280, 8
        margin = 32
        bar_x = (self.width() - bar_w) // 2
        bar_y = self.height() - margin

        progress = len(self.anim_lines) / max(1, len(self.colored_lines)) if self.colored_lines else 0.0
        progress = max(0.0, min(1.0, progress))

        # Тень
        shadow_pen = QPen(QColor(80, 140, 240, 50))
        shadow_pen.setWidthF(10)
        painter.setPen(shadow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 8, 5, 5)

        # Фон бара
        bg_grad = QLinearGradient(bar_x, bar_y, bar_x + bar_w, bar_y)
        bg_grad.setColorAt(0, QColor(20, 30, 55, 200))
        bg_grad.setColorAt(1, QColor(15, 22, 45, 200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_grad))
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 4, 4)

        # Заливка
        if progress > 0:
            fill_w = max(4, int(bar_w * progress))
            fill = QLinearGradient(bar_x, bar_y, bar_x + fill_w, bar_y)
            fill.setColorAt(0, QColor(74, 143, 231, 230))
            fill.setColorAt(1, QColor(208, 143, 255, 230))
            painter.setBrush(QBrush(fill))
            painter.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 4, 4)

        # Текст
        font = QFont("Segoe UI", 10, QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor(180, 200, 230, 240))
        text = f"{len(self.anim_lines)} / {len(self.colored_lines) or '?'} линий  ·  {int(progress * 100)}%"
        painter.drawText(bar_x, bar_y - 10, bar_w, 14, Qt.AlignmentFlag.AlignCenter, text)

    # ────────── Мышь ──────────
    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 1200.0
        new_zoom = max(0.05, min(self.zoom * (1 + delta), 50.0))
        # Зум к курсору
        if new_zoom != self.zoom:
            mouse = event.position()
            cx, cy = self.width() / 2.0, self.height() / 2.0
            # Точка под курсором в мировых координатах
            mx = (mouse.x() - cx - self.pan_x) / self.zoom
            my = (mouse.y() - cy - self.pan_y) / self.zoom
            self.zoom = new_zoom
            self.pan_x = mouse.x() - cx - mx * self.zoom
            self.pan_y = mouse.y() - cy - my * self.zoom
            self.update()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = True
            self.last_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_panning:
            delta = event.position() - self.last_pos
            self.pan_x += delta.x()
            self.pan_y += delta.y()
            self.last_pos = event.position()
            self.update()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.update()
        event.accept()
