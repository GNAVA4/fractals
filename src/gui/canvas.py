from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QLineF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QLinearGradient, QRadialGradient, QBrush


class FractalCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.colored_lines = []
        self.line_width = 1.5
        
        # Навигация
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.is_panning = False
        self.last_pos = QPointF()

        # Анимация
        self.anim_lines = []
        self._progress_text = ""
        
        # Для градиентного фона
        self._bg_color1 = QColor(8, 12, 24)
        self._bg_color2 = QColor(15, 22, 40)

        self.setMinimumSize(400, 400)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # --- Фон с радиальным градиентом (виньетка) ---
        bg_grad = QRadialGradient(
            float(self.width() / 2), float(self.height() / 2), 
            float(max(self.width(), self.height()) * 0.7),
            float(self.width() / 2), float(self.height() / 2)
        )
        bg_grad.setColorAt(0, QColor(18, 26, 50))
        bg_grad.setColorAt(0.5, QColor(12, 18, 36))
        bg_grad.setColorAt(1, QColor(6, 9, 18))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_grad))
        painter.drawRect(self.rect())

        # --- Тонкая сетка ---
        self._draw_grid(painter)

        # Трансформация координат
        cx, cy = self.width() / 2.0, self.height() / 2.0
        painter.translate(cx + self.pan_x, cy + self.pan_y)
        painter.scale(self.zoom, -self.zoom)

        if not self.colored_lines and not self.anim_lines:
            return

        # --- Основной слой (яркие линии) ---
        draw_lines = self.anim_lines if self.anim_lines else self.colored_lines
        for line, color_hex in draw_lines:
            color = QColor(color_hex)
            
            # Полупрозрачная линия (alpha 240)
            bright_color = QColor(color)
            bright_color.setAlpha(240)
            
            pen = QPen(bright_color)
            pen.setWidthF(self.line_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(QLineF(line.start.x, line.start.y, line.end.x, line.end.y))

        # --- Прогресс-бар ---
        if self._progress_text:
            self._draw_progress(painter)

    def _draw_grid(self, painter):
        """Рисует тонкую сетку на фоне."""
        grid_color = QColor(40, 60, 120, 30)
        pen = QPen(grid_color)
        pen.setWidthF(1)
        painter.setPen(pen)

        step = 50
        w, h = self.width(), self.height()
        
        # Вертикальные линии
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, h)
        
        # Горизонтальные линии  
        for y in range(0, h, step):
            painter.drawLine(0, y, w, y)

    def _draw_progress(self, painter):
        """Рисует прогресс-бар анимации."""
        if not self.colored_lines:
            return
            
        progress = len(self.anim_lines) / max(len(self.colored_lines), 1)
        
        bar_w = 240
        bar_h = 6
        margin = 30
        bar_x = (self.width() - bar_w) // 2
        bar_y = self.height() - margin

        # Тень бара
        shadow_pen = QPen(QColor(0, 100, 255, 40))
        shadow_pen.setWidthF(8)
        painter.setPen(shadow_pen)
        painter.drawRoundedRect(bar_x - 3, bar_y - 3, bar_w + 6, bar_h + 6, 4, 4)

        # Фон бара
        bg_grad = QLinearGradient(bar_x, bar_y, bar_x + bar_w, bar_y)
        bg_grad.setColorAt(0, QColor(20, 30, 55, 180))
        bg_grad.setColorAt(1, QColor(15, 22, 45, 180))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_grad))
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 3, 3)

        # Заполнение
        if progress > 0:
            fill_w = max(4, int(bar_w * progress))
            fill_grad = QLinearGradient(bar_x, bar_y, bar_x + fill_w, bar_y)
            fill_grad.setColorAt(0, QColor(74, 143, 231, 200))
            fill_grad.setColorAt(1, QColor(120, 96, 235, 200))
            painter.setBrush(QBrush(fill_grad))
            painter.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 3, 3)

        # Текст
        font = QFont("Segoe UI", 10, QFont.Weight.Medium)
        painter.setFont(font)
        
        text_color = QColor(160, 184, 216)
        painter.setPen(QColor(text_color))
        
        total_text = f" / {len(self.colored_lines)} линий"
        painter.drawText(bar_x + bar_w // 2, bar_y - 6, 
                        f"{len(self.anim_lines)}{total_text}")

    def set_data(self, colored_lines: list[tuple[object, str]], line_width: float):
        self.colored_lines = colored_lines
        self.line_width = line_width
        self.anim_lines = []
        self._progress_text = ""
        self.update()

    def set_anim_state(self, lines: list[tuple[object, str]], total: int, paused: bool = False):
        self.anim_lines = [(line, c_hex) for line, c_hex in lines] if lines else []
        self._progress_text = f"{len(lines)} / {total}" if total > 0 else ""
        self.update()

    # --- Мышь ---
    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 1200.0
        self.zoom = max(0.05, min(self.zoom * (1 + delta), 50.0))
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
