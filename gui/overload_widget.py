"""
OverloadWidget – widget wskaźnika przebodźcowania.

Wyświetla aktualny score, pasek postępu, informacje o aktywnym oknie
i suwak ręcznej korekty.
"""

from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QLinearGradient
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QProgressBar, QSizePolicy, QGroupBox
)

from core.overload_monitor import OverloadMonitor


class OverloadBar(QWidget):
    """Niestandardowy pasek przebodźcowania z gradientem i animacją."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._score = 0
        self._display_score = 0.0
        self.setFixedHeight(28)
        self.setMinimumWidth(200)

        # Animacja płynnego przejścia
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)  # ~60 FPS
        self._anim_timer.timeout.connect(self._animate)

    def set_score(self, score: int):
        self._score = max(0, min(10, score))
        self._anim_timer.start()

    def _animate(self):
        diff = self._score - self._display_score
        if abs(diff) < 0.05:
            self._display_score = float(self._score)
            self._anim_timer.stop()
        else:
            self._display_score += diff * 0.15
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        radius = h / 2

        # Tło
        painter.setBrush(QColor("#1a2332"))
        painter.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, radius, radius)
        painter.drawPath(path)

        # Wypełnienie z gradientem
        fill_width = max(0, (self._display_score / 10.0) * w)
        if fill_width > 0:
            gradient = QLinearGradient(0, 0, w, 0)
            gradient.setColorAt(0.0, QColor("#10b981"))   # zielony
            gradient.setColorAt(0.3, QColor("#10b981"))
            gradient.setColorAt(0.5, QColor("#f59e0b"))   # żółty
            gradient.setColorAt(0.7, QColor("#f97316"))   # pomarańczowy
            gradient.setColorAt(0.9, QColor("#ef4444"))   # czerwony
            gradient.setColorAt(1.0, QColor("#dc2626"))   # ciemnoczerwony

            painter.setBrush(gradient)
            fill_path = QPainterPath()
            fill_path.addRoundedRect(0, 0, fill_width, h, radius, radius)
            painter.drawPath(fill_path)

        # Tekst score
        painter.setPen(QColor("white"))
        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            0, 0, w, h,
            Qt.AlignmentFlag.AlignCenter,
            f"{self._score}/10"
        )

        painter.end()


class OverloadWidget(QWidget):
    """Widget wskaźnika przebodźcowania z monitorem."""

    def __init__(self, monitor: OverloadMonitor, parent=None):
        super().__init__(parent)
        self.monitor = monitor
        self._setup_ui()

        # Podłączenie sygnałów
        self.monitor.scoreChanged.connect(self._on_score_changed)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # ── Nagłówek ──
        header = QHBoxLayout()
        title = QLabel("🧠 Monitor Przebodźcowania")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self.emoji_label = QLabel("😌")
        self.emoji_label.setFont(QFont("Segoe UI Emoji", 24))
        header.addWidget(self.emoji_label)

        main_layout.addLayout(header)

        # ── Frame z zawartością ──
        content_frame = QFrame()
        content_frame.setObjectName("overloadFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(10)

        # Pasek
        bar_layout = QHBoxLayout()
        self.level_label = QLabel("Niski")
        self.level_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.level_label.setStyleSheet("color: #10b981;")
        bar_layout.addWidget(self.level_label)
        bar_layout.addStretch()

        self.score_label = QLabel("0/10")
        self.score_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        bar_layout.addWidget(self.score_label)

        content_layout.addLayout(bar_layout)

        self.overload_bar = OverloadBar()
        content_layout.addWidget(self.overload_bar)

        # Info o aktywnym oknie
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.window_label = QLabel("Aktywne okno: —")
        self.window_label.setObjectName("activeWindowLabel")
        self.window_label.setWordWrap(True)
        info_layout.addWidget(self.window_label)

        self.process_label = QLabel("Proces: —")
        self.process_label.setStyleSheet("color: #64748b; font-size: 11px; padding: 2px 8px;")
        info_layout.addWidget(self.process_label)

        content_layout.addLayout(info_layout)

        # Średni score
        avg_layout = QHBoxLayout()
        avg_lbl = QLabel("Średnia (ostatnie 20):")
        avg_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        avg_layout.addWidget(avg_lbl)

        self.avg_label = QLabel("0.0")
        self.avg_label.setStyleSheet("color: #f1f5f9; font-size: 12px; font-weight: bold;")
        avg_layout.addWidget(self.avg_label)
        avg_layout.addStretch()

        content_layout.addLayout(avg_layout)

        # ── Ręczna korekta ──
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        content_layout.addWidget(separator)

        override_layout = QHBoxLayout()
        override_label = QLabel("Ręczna korekta:")
        override_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        override_layout.addWidget(override_label)

        self.override_slider = QSlider(Qt.Orientation.Horizontal)
        self.override_slider.setRange(0, 10)
        self.override_slider.setValue(5)
        self.override_slider.setFixedWidth(150)
        override_layout.addWidget(self.override_slider)

        self.override_value = QLabel("5")
        self.override_value.setStyleSheet("color: #f1f5f9; font-size: 12px; min-width: 20px;")
        self.override_slider.valueChanged.connect(
            lambda v: self.override_value.setText(str(v))
        )
        override_layout.addWidget(self.override_value)

        self.apply_override_btn = QPushButton("Zastosuj")
        self.apply_override_btn.setStyleSheet("""
            QPushButton {
                background: #7c3aed; color: white;
                border: none; border-radius: 6px;
                padding: 6px 12px; font-size: 11px;
            }
            QPushButton:hover { background: #8b5cf6; }
        """)
        self.apply_override_btn.clicked.connect(self._apply_override)
        override_layout.addWidget(self.apply_override_btn)

        self.reset_override_btn = QPushButton("Reset")
        self.reset_override_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #94a3b8;
                border: 1px solid #334155; border-radius: 6px;
                padding: 6px 12px; font-size: 11px;
            }
            QPushButton:hover { color: #f1f5f9; border-color: #94a3b8; }
        """)
        self.reset_override_btn.clicked.connect(self._reset_override)
        override_layout.addWidget(self.reset_override_btn)

        content_layout.addLayout(override_layout)

        main_layout.addWidget(content_frame)

    def _on_score_changed(self, score: int, title: str, process: str):
        """Aktualizuj widgety po zmianie score."""
        self.overload_bar.set_score(score)
        self.score_label.setText(f"{score}/10")

        # Poziom
        level_name = OverloadMonitor.get_level_name(score)
        level_color = OverloadMonitor.get_level_color(score)
        self.level_label.setText(level_name)
        self.level_label.setStyleSheet(f"color: {level_color}; font-weight: bold;")

        # Emoji
        self.emoji_label.setText(OverloadMonitor.get_level_emoji(score))

        # Info o oknie
        display_title = title[:80] + "..." if len(title) > 80 else title
        self.window_label.setText(f"Aktywne okno: {display_title or '—'}")
        self.process_label.setText(f"Proces: {process or '—'}")

        # Średnia
        avg = self.monitor.get_average_score()
        self.avg_label.setText(f"{avg:.1f}")

    def _apply_override(self):
        """Zastosuj ręczną korektę dla bieżącego procesu."""
        process = self.monitor.current_process
        if process:
            value = self.override_slider.value()
            self.monitor.set_override(process, value)

    def _reset_override(self):
        """Usuń ręczną korektę dla bieżącego procesu."""
        process = self.monitor.current_process
        if process:
            self.monitor.remove_override(process)
