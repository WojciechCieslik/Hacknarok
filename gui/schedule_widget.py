"""
ScheduleWidget – widget harmonogramu automatycznego przełączania.

Wyświetla listę wpisów harmonogramu z możliwością dodawania i usuwania.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QFrame, QScrollArea,
    QGroupBox, QSizePolicy, QMessageBox
)

from core.scheduler import Scheduler, ScheduleEntry, DAY_NAMES


class ScheduleEntryWidget(QFrame):
    """Widget pojedynczego wpisu harmonogramu."""

    removeRequested = Signal(int)
    changed = Signal()

    def __init__(self, index: int, entry: ScheduleEntry, profile_names: list[str],
                 parent=None):
        super().__init__(parent)
        self.index = index
        self.setObjectName("cardFrame")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        # Checkbox włączone/wyłączone
        self.enabled_cb = QCheckBox()
        self.enabled_cb.setChecked(entry.enabled)
        self.enabled_cb.stateChanged.connect(lambda: self.changed.emit())
        layout.addWidget(self.enabled_cb)

        # Godzina
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(entry.hour)
        self.hour_spin.setPrefix("Godz: ")
        self.hour_spin.setFixedWidth(100)
        self.hour_spin.valueChanged.connect(lambda: self.changed.emit())
        layout.addWidget(self.hour_spin)

        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(entry.minute)
        self.minute_spin.setPrefix("Min: ")
        self.minute_spin.setFixedWidth(100)
        self.minute_spin.valueChanged.connect(lambda: self.changed.emit())
        layout.addWidget(self.minute_spin)

        # Profil
        self.profile_combo = QComboBox()
        for name in profile_names:
            self.profile_combo.addItem(name)
        idx = profile_names.index(entry.profile_name) if entry.profile_name in profile_names else 0
        self.profile_combo.setCurrentIndex(idx)
        self.profile_combo.setMinimumWidth(120)
        self.profile_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        layout.addWidget(self.profile_combo)

        # Dni tygodnia
        self.day_checks: list[QCheckBox] = []
        days_frame = QFrame()
        days_layout = QHBoxLayout(days_frame)
        days_layout.setContentsMargins(0, 0, 0, 0)
        days_layout.setSpacing(2)
        for i, day_name in enumerate(DAY_NAMES):
            cb = QCheckBox(day_name)
            cb.setChecked(i in entry.days)
            cb.setStyleSheet("font-size: 11px;")
            cb.stateChanged.connect(lambda: self.changed.emit())
            self.day_checks.append(cb)
            days_layout.addWidget(cb)
        layout.addWidget(days_frame)

        layout.addStretch()

        # Usuwanie
        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(28, 28)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                color: #ef4444; font-size: 16px; font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background: rgba(239,68,68,0.1); }
        """)
        remove_btn.clicked.connect(lambda: self.removeRequested.emit(self.index))
        layout.addWidget(remove_btn)

    def get_entry(self) -> ScheduleEntry:
        """Zwróć ScheduleEntry z bieżących wartości."""
        days = [i for i, cb in enumerate(self.day_checks) if cb.isChecked()]
        return ScheduleEntry(
            profile_name=self.profile_combo.currentText(),
            hour=self.hour_spin.value(),
            minute=self.minute_spin.value(),
            days=days if days else list(range(7)),
            enabled=self.enabled_cb.isChecked(),
        )


class ScheduleWidget(QWidget):
    """Widget harmonogramu z listą wpisów i przyciskami zarządzania."""

    def __init__(self, scheduler: Scheduler, profile_names: list[str], parent=None):
        super().__init__(parent)
        self.scheduler = scheduler
        self.profile_names = profile_names
        self._entry_widgets: list[ScheduleEntryWidget] = []

        self._setup_ui()
        self._refresh()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Nagłówek
        header = QHBoxLayout()
        title = QLabel("📅 Harmonogram automatycznego przełączania")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("➕ Dodaj regułę")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self._add_entry)
        header.addWidget(add_btn)

        main_layout.addLayout(header)

        # Kontener na wpisy
        self.entries_layout = QVBoxLayout()
        self.entries_layout.setSpacing(6)
        main_layout.addLayout(self.entries_layout)

        # Info
        self.empty_label = QLabel(
            "Brak reguł harmonogramu. Dodaj regułę, aby automatycznie przełączać profile."
        )
        self.empty_label.setStyleSheet("color: #64748b; font-style: italic; padding: 16px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.empty_label)

        main_layout.addStretch()

    def _refresh(self):
        # Wyczyść
        for w in self._entry_widgets:
            self.entries_layout.removeWidget(w)
            w.deleteLater()
        self._entry_widgets.clear()

        # Odbuduj
        for i, entry in enumerate(self.scheduler.entries):
            widget = ScheduleEntryWidget(i, entry, self.profile_names)
            widget.removeRequested.connect(self._remove_entry)
            widget.changed.connect(self._on_change)
            self._entry_widgets.append(widget)
            self.entries_layout.addWidget(widget)

        self.empty_label.setVisible(len(self._entry_widgets) == 0)

    def _add_entry(self):
        if not self.profile_names:
            QMessageBox.warning(self, "Brak profili", "Najpierw utwórz profil!")
            return
        new_entry = ScheduleEntry(
            profile_name=self.profile_names[0],
            hour=9, minute=0,
            days=list(range(5)),
        )
        self.scheduler.add_entry(new_entry)
        self._refresh()

    def _remove_entry(self, index: int):
        self.scheduler.remove_entry(index)
        self._refresh()

    def _on_change(self):
        """Zapisz wszystkie zmiany."""
        self.scheduler.entries = [w.get_entry() for w in self._entry_widgets]
        self.scheduler.save()

    def update_profile_names(self, names: list[str]):
        """Zaktualizuj listę dostępnych profili."""
        self.profile_names = names
        self._refresh()
