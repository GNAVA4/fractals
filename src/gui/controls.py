import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QSpinBox, QDoubleSpinBox, QCheckBox, QSlider, QPushButton
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QRectF, QSize
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QLinearGradient, QRadialGradient,
    QPalette, QBrush
)
from src.core.types import FractalConfig


class GlassPanel(QWidget):
    """Стеклянная панель с градиентным фоном и blur-эффектом."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gradient_start = QColor(20, 30, 60, 180)
        self._gradient_end = QColor(10, 15, 35, 200)
        self._border_color = QColor(70, 120, 220, 80)
        self._glow_color = QColor(60, 110, 210, 40)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Основной градиент с прозрачностью
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0.0, QColor(25, 35, 70, 190))
        gradient.setColorAt(0.3, QColor(20, 30, 60, 200))
        gradient.setColorAt(0.7, QColor(15, 22, 48, 210))
        gradient.setColorAt(1.0, QColor(10, 16, 38, 220))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(self.rect(), 14, 14)
        
        # Верхний блик (glass highlight)
        highlight = QLinearGradient(0, 0, 0, self.height() * 0.35)
        highlight.setColorAt(0.0, QColor(255, 255, 255, 35))
        highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(highlight))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -int(self.height() * 0.35)), 14, 14)
        
        # Внешняя рамка с glow
        pen = QPen(self._border_color)
        pen.setWidthF(1.2)
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)
        
        # Внутренний glow
        inner_glow = QLinearGradient(0, self.height(), 0, 0)
        inner_glow.setColorAt(0.0, QColor(60, 120, 230, 50))
        inner_glow.setColorAt(0.3, QColor(60, 120, 230, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(inner_glow))
        painter.drawRoundedRect(self.rect().adjusted(4, 4, -4, -4), 12, 12)


class GlassSpinbox(QWidget):
    """Стеклянный spinbox с proper paint."""
    
    def __init__(self, min_val, max_val, default, step=0.1, parent=None):
        super().__init__(parent)
        self.is_double = step < 1 or step == 0.1
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        self.spin = QDoubleSpinBox() if self.is_double else QSpinBox()
        self.spin.setRange(min_val, max_val)
        self.spin.setValue(default)
        self.spin.setSingleStep(step)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Кнопки
        self.up_btn = QPushButton("▲")
        self.down_btn = QPushButton("▼")
        self.up_btn.setFixedSize(18, 14)
        self.down_btn.setFixedSize(18, 14)
        self.up_btn.setCursor(Qt.CursorShape.ArrowCursor)
        self.down_btn.setCursor(Qt.CursorShape.ArrowCursor)
        
        layout.addWidget(self.spin, 1)
        layout.addWidget(self.up_btn)
        layout.addWidget(self.down_btn)
        
        self.up_btn.clicked.connect(lambda: self.spin.stepUp())
        self.down_btn.clicked.connect(lambda: self.spin.stepDown())
        
    def value(self):
        return self.spin.value() if self.is_double else self.spin.value()


class GlassComboBox(QWidget):
    """Стеклянный combobox."""
    
    def __init__(self, items, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)
        
        self.combo = QComboBox()
        self.combo.addItems(items)
        self.combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.combo.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Стили для dropdown
        self.combo.setStyleSheet("""
            QComboBox {
                background: rgba(12, 18, 36, 0.9);
                border: 1px solid rgba(70, 120, 210, 0.5);
                border-radius: 8px;
                padding: 6px 12px;
                color: #c4daf8;
                font-size: 12px;
                min-height: 30px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 1px solid rgba(70, 120, 210, 0.3);
                margin-right: 4px;
            }
            QComboBox QAbstractItemView {
                background: rgba(15, 22, 44, 0.98);
                border: 1px solid rgba(70, 120, 210, 0.6);
                selection-background-color: rgba(50, 90, 180, 0.5);
                selection-color: #e0ecff;
                outline: none;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        
        layout.addWidget(self.combo, 1)


class GlassCheckBox(QWidget):
    """Стеклянный чекбокс."""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.isChecked_val = False
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        
        self.check_indicator = QWidget()
        self.check_indicator.setFixedSize(18, 18)
        
        self.label = QLabel(text)
        self.label.setStyleSheet("color: #a0b8d8; font-size: 12px;")
        self.label.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout.addWidget(self.check_indicator)
        layout.addWidget(self.label, 1)
        
    def toggle(self):
        self.isChecked_val = not self.isChecked_val
        self.update()
        self.toggled.emit(self.isChecked_val)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
            super().mousePressEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Индикатор чекбокса
        x = 4
        y = (self.height() - 18) // 2
        
        if self.isChecked_val:
            # Градиентный фон
            grad = QRadialGradient(9.0, 9.0, 10.0, 9.0, 9.0)
            grad.setColorAt(0, QColor(74, 143, 231))
            grad.setColorAt(1, QColor(108, 92, 231))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(x + 1, y + 1, 16, 16, 4, 4)
            
            # Галочка
            pen = QPen(QColor(255, 255, 255, 240))
            pen.setWidthF(2.5)
            painter.setPen(pen)
            points = [QPoint(x + 4, y + 9), QPoint(x + 7, y + 13), QPoint(x + 14, y + 5)]
            painter.drawPolyline(*points)
        else:
            # Пустой индикатор
            painter.setPen(QPen(QColor(60, 100, 180, 120), 1.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(x + 1, y + 1, 16, 16, 4, 4)
    
    def isChecked(self):
        return self.isChecked_val


class GlassSlider(QWidget):
    """Стеклянный слайдер."""
    
    value_changed = pyqtSignal(int)
    
    def __init__(self, min_val, max_val, default, parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.current_value = default
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)
        
        # Track (фон слайдера)
        self.track = QWidget()
        self.track.setFixedHeight(8)
        
        # Handle
        self.handle = QWidget()
        self.handle.setFixedSize(20, 20)
        self.handle.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout.addWidget(self.track)
        layout.addWidget(self.handle)
        
        # Позиция handle
        self._update_handle_position(default)
    
    def _update_handle_position(self, value):
        if self.max_val == self.min_val:
            return
        ratio = (value - self.min_val) / (self.max_val - self.min_val)
        track_width = self.track.width()
        x = int(ratio * (track_width - 20))
        self.handle.move(x, 0)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._handle_value(event.pos())
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._handle_value(event.pos())
    
    def _handle_value(self, pos):
        track_width = self.track.width()
        x = max(0, min(pos.x(), track_width - 20))
        ratio = x / (track_width - 20) if track_width > 20 else 0.5
        value = int(self.min_val + ratio * (self.max_val - self.min_val))
        value = max(self.min_val, min(value, self.max_val))
        
        if value != self.current_value:
            self.current_value = value
            self._update_handle_position(value)
            self.value_changed.emit(value)


class GlassButton(QPushButton):
    """Стеклянная кнопка с paint-эффектами."""
    
    def __init__(self, text, gradient_colors=None, parent=None):
        super().__init__(text, parent)
        self._default_colors = gradient_colors or [
            QColor(58, 111, 216), QColor(91, 76, 199)
        ]
        self._hovered = False
        self._pressed = False
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(38)
        
    def setHover(self, hovered):
        self._hovered = hovered
        self.update()
    
    def setPressed(self, pressed):
        self._pressed = pressed
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        
        if self.isChecked():
            # Активное состояние — красный градиент
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0, QColor(232, 90, 58))
            grad.setColorAt(1, QColor(199, 76, 199))
        elif self._pressed:
            # Pressed — чуть ярче
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0, QColor(82, 135, 240))
            grad.setColorAt(1, QColor(115, 96, 231))
        elif self._hovered:
            # Hover — чуть ярче default
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0, QColor(74, 143, 240))
            grad.setColorAt(1, QColor(120, 96, 235))
        else:
            # Default
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0, self._default_colors[0])
            grad.setColorAt(1, self._default_colors[1])
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(self.rect(), 9, 9)
        
        # Верхний блик
        highlight = QLinearGradient(0, 0, 0, h * 0.45)
        highlight.setColorAt(0, QColor(255, 255, 255, 30))
        highlight.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(highlight))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -int(h * 0.45)), 9, 9)

        # Текст кнопки
        text_color = QColor(255, 255, 255, 230 if not self.isChecked() else 255)
        font = painter.font()
        font.setBold(True)
        font.setPointSizeF(10.5)
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())


class ControlsPanel(QWidget):
    parameters_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        # Включаем translucent background для всей панели
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        self._build_ui()
        self._connect_signals()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Фон панели — глубокий тёмный градиент
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(14, 20, 40, 230))
        gradient.setColorAt(0.5, QColor(18, 26, 50, 235))
        gradient.setColorAt(1.0, QColor(12, 17, 35, 240))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(self.rect(), 18, 18)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 16, 20, 16)

        # Заголовок с градиентным текстом
        title_label = QLabel("⬡ Параметры")
        title_label.setStyleSheet("""
            color: #c8daf8; 
            font-size: 17px; 
            font-weight: bold;
            padding: 4px 0;
        """)
        layout.addWidget(title_label)

        # Glass-контейнер
        self._panel = GlassPanel()
        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setSpacing(12)
        panel_layout.setContentsMargins(16, 14, 16, 14)

        # Тип фрактала
        self.type_combo = GlassComboBox([
            "sierpinski", "t_fractal", "h_fractal", 
            "koch", "tree", "lightning"
        ])
        panel_layout.addWidget(self._section("Тип фрактала:", self.type_combo.combo))

        # Spinbox-поля
        self.depth_spin = self._glass_spin(panel_layout, "Глубина:", 1, 12, 4)
        self.scale_spin = self._glass_dspin(panel_layout, "Масштаб рекурсии:", 0.1, 0.9, 0.5)
        self.display_spin = self._glass_dspin(panel_layout, "Масштаб отображения:", 50, 800, 300)
        self.rot_spin = self._glass_dspin(panel_layout, "Поворот (°):", -360, 360, 0)
        self.width_spin = self._glass_dspin(panel_layout, "Толщина линий:", 0.5, 5.0, 1.5, step=0.5)
        self.tree_spread_spin = self._glass_dspin(panel_layout, "Угол ветвления (°):", 5, 60, 25)

        # Раскраска
        self.color_combo = GlassComboBox(["gradient", "rainbow", "pos"])
        panel_layout.addWidget(self._section("Раскраска:", self.color_combo.combo))

        # Симметрия
        self.sym_x_check = GlassCheckBox("Симметрия X")
        self.sym_y_check = GlassCheckBox("Симметрия Y")
        panel_layout.addWidget(self.sym_x_check)
        panel_layout.addWidget(self.sym_y_check)

        # Радиальная симметрия
        sym_row = QWidget()
        sym_layout = QHBoxLayout(sym_row)
        sym_layout.setContentsMargins(0, 0, 0, 0)
        sym_layout.setSpacing(8)
        
        sym_label = QLabel("Радиальная (N):")
        sym_label.setStyleSheet("color: #a0b8d8; font-size: 12px;")
        
        self.radial_spin = GlassSpinbox(0, 12, 0)
        
        sym_layout.addWidget(sym_label)
        sym_layout.addWidget(self.radial_spin, 1)
        panel_layout.addWidget(sym_row)

        # Скорость анимации
        anim_frame = GlassPanel()
        anim_layout = QVBoxLayout(anim_frame)
        anim_layout.setSpacing(4)
        anim_layout.setContentsMargins(16, 10, 16, 10)
        
        speed_label = QLabel("Скорость анимации:")
        speed_label.setStyleSheet("color: #a0b8d8; font-size: 12px;")
        anim_layout.addWidget(speed_label)

        self.speed_slider = GlassSlider(1, 50, 15)
        self.speed_slider.value_changed.connect(self._on_speed_change)
        anim_layout.addWidget(self.speed_slider)

        self.speed_label_widget = QLabel("15 линий/сек")
        self.speed_label_widget.setStyleSheet("""
            color: #7a94b8; 
            font-size: 11px; 
            text-align: center;
            padding: 2px;
        """)
        anim_layout.addWidget(self.speed_label_widget)

        panel_layout.addWidget(anim_frame)

        # Кнопки анимации
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 4, 0, 0)
        btn_layout.setSpacing(10)
        
        self.play_btn = GlassButton("▶ Анимация", [
            QColor(58, 111, 216), QColor(91, 76, 199)
        ])
        btn_layout.addWidget(self.play_btn, 1)

        self.reset_btn = GlassButton("↺ Сброс", [
            QColor(30, 45, 80), QColor(25, 35, 65)
        ])
        self.reset_btn.setStyleSheet("""
            QPushButton {
                color: #a0b4d0;
                font-size: 12px;
                padding: 8px 16px;
            }
        """)
        self.reset_btn.clicked.connect(self._reset_animation)
        btn_layout.addWidget(self.reset_btn, 1)
        
        panel_layout.addWidget(btn_row)

        layout.addWidget(self._panel)
        
        # Параметры молнии
        lightning_frame = GlassPanel()
        lightning_layout = QVBoxLayout(lightning_frame)
        lightning_layout.setSpacing(6)
        lightning_layout.setContentsMargins(16, 10, 16, 10)

        lightning_title = QLabel("⚡ Молния")
        lightning_title.setStyleSheet("""
            color: #c8daf8; 
            font-size: 14px; 
            font-weight: bold;
            padding: 2px 0;
        """)
        lightning_layout.addWidget(lightning_title)

        self.seed_spin = self._glass_spin(lightning_layout, "Seed:", 0, 9999, 42)
        self.rough_spin = self._glass_dspin(lightning_layout, "Шероховатость:", 0.0, 1.5, 0.8)

        panel_layout.addWidget(lightning_frame)

        layout.addStretch()
    
    def _section(self, label_text, widget):
        """Оборачивает элемент в glass-секцию."""
        frame = QWidget()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)
        
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #a0b8d8; font-size: 12px;")
        
        layout.addWidget(lbl)
        layout.addWidget(widget)
        return frame
    
    def _glass_spin(self, parent_layout, label, mn, mx, default):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(8)
        
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #a0b8d8; font-size: 12px;")
        
        spin = GlassSpinbox(mn, mx, default)
        spin.setStyleSheet("""
            background: transparent;
        """)
        
        row_layout.addWidget(lbl)
        row_layout.addWidget(spin, 1)
        parent_layout.addWidget(row)
        return spin

    def _glass_dspin(self, parent_layout, label, mn, mx, default, step=0.1):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(8)
        
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #a0b8d8; font-size: 12px;")
        
        spin = GlassSpinbox(mn, mx, default, step=step)
        
        row_layout.addWidget(lbl)
        row_layout.addWidget(spin, 1)
        parent_layout.addWidget(row)
        return spin

    def _connect_signals(self):
        for w in self.findChildren((QComboBox, QSpinBox)):
            if hasattr(w, 'valueChanged'): 
                w.valueChanged.connect(self._on_param_changed)
            elif hasattr(w, 'currentIndexChanged'): 
                w.currentIndexChanged.connect(self._on_param_changed)
        
        # Подключаем кастомные виджеты
        for cb in self.findChildren(GlassCheckBox):
            cb.toggled.connect(self._on_param_changed)
        
        if hasattr(self, 'speed_slider') and self.speed_slider:
            self.speed_slider.value_changed.connect(self._on_speed_change)
    
    def _on_param_changed(self):
        self.parameters_changed.emit()
    
    def _toggle_animation(self):
        checked = self.play_btn.isChecked()
        self.parameters_changed.emit()

    def _reset_animation(self):
        self.play_btn.setChecked(False)
        self.parameters_changed.emit()

    def _on_speed_change(self, value):
        self.speed_label_widget.setText(f"{value} линий/сек")
    
    def get_config(self) -> FractalConfig:
        return FractalConfig(
            fractal_type=self.type_combo.combo.currentText(),
            depth=int(self.depth_spin.spin.value()),
            scale=self.scale_spin.spin.value(),
            display_scale=self.display_spin.spin.value(),
            rotation_deg=self.rot_spin.spin.value(),
            line_width=self.width_spin.spin.value(),
            color_mode=self.color_combo.combo.currentText(),
            tree_spread=self.tree_spread_spin.spin.value(),
            symmetry_x=self.sym_x_check.isChecked(),
            symmetry_y=self.sym_y_check.isChecked(),
            radial_symmetry=int(self.radial_spin.value()),
            seed=int(self.seed_spin.spin.value()),
            roughness=self.rough_spin.spin.value()
        )

    def get_animation_speed(self) -> int:
        return self.speed_slider.current_value

    def is_animation_playing(self) -> bool:
        return self.play_btn.isChecked()
