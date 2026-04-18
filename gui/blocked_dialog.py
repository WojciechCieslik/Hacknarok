"""
BlockedAppNotification – powiadomienie o zablokowanej aplikacji.

Pojawia się w dolnym-prawym rogu ekranu gdy profil zawiesza zabronioną aplikację.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
)


class BlockedAppNotification(QWidget):
    """Niemodalny dymek w rogu ekranu informujący o zablokowanej aplikacji."""

    def __init__(self, app_display_name: str, profile_name: str, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedSize(340, 130)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - 360, screen.bottom() - 150)

        self._build_ui(app_display_name, profile_name)

        QTimer.singleShot(6000, self.close)
        self.show()

    def _build_ui(self, app_name: str, profile_name: str):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border: 2px solid #7c3aed;
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 13, 16, 11)
        layout.setSpacing(7)

        # Nagłówek
        header = QHBoxLayout()
        icon_lbl = QLabel("🚫")
        icon_lbl.setStyleSheet("font-size: 20px; background: transparent; border: none;")
        title_lbl = QLabel("Aplikacja zablokowana")
        title_lbl.setStyleSheet(
            "color: #f1f5f9; font-weight: bold; font-size: 13px;"
            " background: transparent; border: none;"
        )
        header.addWidget(icon_lbl)
        header.addWidget(title_lbl, 1)
        layout.addLayout(header)

        # Treść
        msg = QLabel(
            f"<span style='color:#f1f5f9; font-weight:bold'>{app_name}</span>"
            f"<span style='color:#94a3b8'> jest zablokowana przez profil </span>"
            f"<span style='color:#a78bfa; font-weight:bold'>{profile_name}</span>"
        )
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 12px; background: transparent; border: none;")
        layout.addWidget(msg)

        # Przycisk
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        ok_btn = QPushButton("Rozumiem")
        ok_btn.setFixedHeight(26)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #7c3aed;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 11px;
                padding: 0 14px;
            }
            QPushButton:hover { background: #6d28d9; }
        """)
        ok_btn.clicked.connect(self.close)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        outer.addWidget(frame)
