import traceback
from PyQt6.QtWidgets import QMainWindow, QHBoxLayout, QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QFont, QBrush


class GlassWindow(QMainWindow):
    """Главное окно с glass-фоном через paintEvent."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Фракталы — Liquid Glass")
        self.resize(1200, 750)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(14, 14, 14, 14)

        # Панель управления (заполняется потомком)
        self.controls_frame = QWidget()
        self.controls_frame.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.addWidget(self.controls_frame)
        
        main_layout.addWidget(controls_container, 1)

        from src.gui.canvas import FractalCanvas
        self.canvas = FractalCanvas()
        main_layout.addWidget(self.canvas, 3)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(10, 14, 26))
        gradient.setColorAt(0.3, QColor(15, 20, 38))
        gradient.setColorAt(0.7, QColor(12, 17, 32))
        gradient.setColorAt(1.0, QColor(8, 12, 24))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(self.rect())


from src.gui.canvas import FractalCanvas
from src.gui.controls import ControlsPanel
from src.bridge import generate_fractal, generate_fractal_batched


class MainWindow(GlassWindow):
    def __init__(self):
        super().__init__()

        self.controls = ControlsPanel()
        
        from PyQt6.QtWidgets import QVBoxLayout
        controls_layout = QVBoxLayout(self.controls_frame)
        controls_layout.setContentsMargins(4, 4, 4, 4)
        controls_layout.setSpacing(8)
        controls_layout.addWidget(self.controls)

        # Hover tracking
        self._btn_hover_map = {}

        # Timers
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(150)
        self.update_timer.timeout.connect(self._apply_changes)

        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._anim_step)
        
        # State
        self._batch_iterator = None
        self._total_batches = 0
        self._accumulated_lines = []

        # Connect signals
        self.controls.parameters_changed.connect(self._on_parameter_change)
        self.controls.play_btn.clicked.connect(self._toggle_animation)
        self.controls.reset_btn.clicked.connect(self._reset_animation)

        # Hover effects via event filters
        self._install_hover_filter(self.controls.play_btn, "play")
        self._install_hover_filter(self.controls.reset_btn, "reset")

        self._apply_changes()

    def _install_hover_filter(self, btn, name):
        """Устанавливаем hover-эффект на кнопку."""
        btn.enterEvent = lambda e: self._set_btn_hover(name, True)
        btn.leaveEvent = lambda e: self._set_btn_hover(name, False)

    def _set_btn_hover(self, name, hovered):
        if name == "play":
            self.controls.play_btn.setHover(hovered)
        elif name == "reset":
            self.controls.reset_btn.setHover(hovered)

    def _toggle_animation(self):
        playing = self.controls.is_animation_playing()
        
        if not playing:
            self.controls.play_btn.setChecked(True)
            self._start_animation()
        else:
            self.controls.play_btn.setChecked(False)
            self.anim_timer.stop()

    def _start_animation(self):
        config = self.controls.get_config()
        speed = self.controls.get_animation_speed()
        interval = max(10, 1000 // speed)
        
        try:
            self._batch_iterator = generate_fractal_batched(config)
            first_result = next(self._batch_iterator)
            colored_lines, idx, total, mode = first_result
            
            if mode == 'accumulate':
                self._accumulated_lines = list(colored_lines)
            else:
                self._accumulated_lines = list(colored_lines)
            
            self._total_batches = total
                
            self.canvas.set_anim_state(self._accumulated_lines, total, False)
            
            self.anim_timer.start(interval)
        except StopIteration:
            pass
        except Exception as e:
            print(f"⚠️ Ошибка анимации: {e}")
            traceback.print_exc()

    def _anim_step(self):
        try:
            colored_lines, idx, total, mode = next(self._batch_iterator)
            
            if mode == 'accumulate':
                self._accumulated_lines.extend(colored_lines)
            
            self.canvas.set_anim_state(self._accumulated_lines, total, False)
        except StopIteration:
            self.anim_timer.stop()
            config = self.controls.get_config()
            try:
                full_lines = generate_fractal(config)
                self.canvas.set_data(full_lines, config.line_width)
            except Exception as e:
                print(f"⚠️ Ошибка генерации финала: {e}")
                traceback.print_exc()

    def _reset_animation(self):
        self.anim_timer.stop()
        self.controls.play_btn.setChecked(False)
        self._batch_iterator = None
        self._accumulated_lines = []
        config = self.controls.get_config()
        try:
            full_lines = generate_fractal(config)
            self.canvas.set_data(full_lines, config.line_width)
        except Exception as e:
            print(f"⚠️ Ошибка генерации: {e}")
            traceback.print_exc()

    def _on_parameter_change(self):
        speed = self.controls.get_animation_speed()
        self.controls.speed_label_widget.setText(f"{speed} линий/сек")
        
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
        except Exception as e:
            print(f"⚠️ Ошибка генерации: {e}")
            traceback.print_exc()
