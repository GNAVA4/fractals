import logging
import traceback
from PyQt6.QtWidgets import QMainWindow, QHBoxLayout, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QBrush

from src.gui.canvas import FractalCanvas
from src.gui.controls import ControlsPanel
from src.bridge import generate_fractal, generate_fractal_batched

log = logging.getLogger(__name__)


class GlassWindow(QMainWindow):
    """Главное окно с glass-фоном."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Фракталы — Liquid Glass")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(14, 14, 14, 14)

        # Левая колонка — управление
        self.controls_frame = QWidget()
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addWidget(self.controls_frame)
        controls_container.setMaximumWidth(360)
        controls_container.setMinimumWidth(320)
        main_layout.addWidget(controls_container, 0)

        # Правая колонка — canvas
        self.canvas = FractalCanvas()
        main_layout.addWidget(self.canvas, 1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(8, 12, 24))
        gradient.setColorAt(0.3, QColor(14, 18, 36))
        gradient.setColorAt(0.7, QColor(11, 15, 30))
        gradient.setColorAt(1.0, QColor(6, 10, 20))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(self.rect())


class MainWindow(GlassWindow):
    def __init__(self):
        super().__init__()

        self.controls = ControlsPanel()
        controls_layout = QVBoxLayout(self.controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)
        controls_layout.addWidget(self.controls)

        # Таймеры
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(150)
        self.update_timer.timeout.connect(self._apply_changes)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._anim_step)

        # Состояние анимации
        self._batch_iterator = None
        self._total_batches = 0
        self._accumulated_lines: list = []

        # Сигналы
        self.controls.parameters_changed.connect(self._on_parameter_change)
        self.controls.play_btn.clicked.connect(self._toggle_animation)
        self.controls.reset_btn.clicked.connect(self._reset_animation)

        self._apply_changes()

    # ────────── Анимация ──────────
    def _toggle_animation(self):
        if self.controls.is_animation_playing():
            # play_btn уже в checked-состоянии после клика → запускаем
            self._start_animation()
        else:
            self.anim_timer.stop()

    def _start_animation(self):
        config = self.controls.get_config()
        speed = self.controls.get_animation_speed()
        interval = max(10, 1000 // max(1, speed))

        try:
            self._batch_iterator = generate_fractal_batched(config)
            colored_lines, _idx, total = next(self._batch_iterator)
            self._accumulated_lines = list(colored_lines)
            self._total_batches = total
            self.canvas.set_anim_state(self._accumulated_lines, total)
            self.anim_timer.start(interval)
        except StopIteration:
            self.controls.play_btn.setChecked(False)
        except Exception:
            log.error("Анимация не запустилась:\n%s", traceback.format_exc())
            self.controls.play_btn.setChecked(False)

    def _anim_step(self):
        try:
            colored_lines, _idx, _total = next(self._batch_iterator)
            self._accumulated_lines.extend(colored_lines)
            self.canvas.set_anim_state(self._accumulated_lines, self._total_batches)
        except StopIteration:
            self.anim_timer.stop()
            self.controls.play_btn.setChecked(False)
            # Финал — используем накопленные линии (симметрии и цвет уже применены в batched)
            config = self.controls.get_config()
            self.canvas.set_data(self._accumulated_lines, config.line_width)
        except Exception:
            log.error("Ошибка шага анимации:\n%s", traceback.format_exc())
            self.anim_timer.stop()
            self.controls.play_btn.setChecked(False)

    def _reset_animation(self):
        self.anim_timer.stop()
        self.controls.play_btn.setChecked(False)
        self._batch_iterator = None
        self._accumulated_lines = []
        self._apply_changes()

    def _on_parameter_change(self):
        if self.controls.is_animation_playing():
            self.anim_timer.stop()
            self._start_animation()
        else:
            self.update_timer.start()

    def _apply_changes(self):
        config = self.controls.get_config()
        try:
            colored_lines = generate_fractal(config)
            self.canvas.set_data(colored_lines, config.line_width)
        except Exception:
            log.error("Ошибка генерации:\n%s", traceback.format_exc())
