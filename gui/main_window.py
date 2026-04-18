"""
MainWindow – główne okno aplikacji Context Switcher Pro.

Zawiera karty profili, monitor przebodźcowania i harmonogram.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QTabWidget,
    QSystemTrayIcon, QMenu, QMessageBox, QSizePolicy,
    QApplication
)

from core.profile_manager import ProfileManager, Profile
from core.scheduler import Scheduler
from core.overload_monitor import OverloadMonitor
from gui.profile_card import ProfileCard
from gui.profile_editor import ProfileEditorDialog
from gui.schedule_widget import ScheduleWidget
from gui.overload_widget import OverloadWidget


class MainWindow(QMainWindow):
    """Główne okno Context Switcher Pro."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Context Switcher Pro")
        self.setMinimumSize(900, 700)
        self.resize(1050, 780)

        # ── Inicjalizacja komponentów ──
        self.profile_manager = ProfileManager()
        self.scheduler = Scheduler()
        self.monitor = OverloadMonitor()

        # Połączenia sygnałów
        self.profile_manager.profileChanged.connect(self._on_profile_changed)
        self.profile_manager.profilesUpdated.connect(self._refresh_profiles)
        self.scheduler.scheduleTriggered.connect(self._on_schedule_trigger)

        # Timer blokady procesów (co 5s)
        self._block_timer = QTimer(self)
        self._block_timer.setInterval(5000)
        self._block_timer.timeout.connect(self.profile_manager.enforce_blocks)

        # ── Budowa UI ──
        self._setup_ui()
        self._setup_tray()

        # Uruchomienie
        self.scheduler.start()
        self.monitor.start()
        self._block_timer.start()

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # ── Nagłówek ──
        header = self._build_header()
        main_layout.addLayout(header)

        # ── Separator ──
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(sep)

        # ── Zakładki ──
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Tab 1: Profile
        profiles_tab = QWidget()
        profiles_layout = QVBoxLayout(profiles_tab)
        profiles_layout.setContentsMargins(0, 16, 0, 0)

        # Kontener kart profili
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.cards_scroll.setStyleSheet("QScrollArea { border: none; }")

        self.cards_container = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(16)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.cards_scroll.setWidget(self.cards_container)
        profiles_layout.addWidget(self.cards_scroll)

        # Monitor przebodźcowania (na dole)
        self.overload_widget = OverloadWidget(self.monitor)
        profiles_layout.addWidget(self.overload_widget)

        self.tabs.addTab(profiles_tab, "🖥️ Profile")

        # Tab 2: Harmonogram
        schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(schedule_tab)
        schedule_layout.setContentsMargins(0, 16, 0, 0)

        profile_names = [p.name for p in self.profile_manager.profiles]
        self.schedule_widget = ScheduleWidget(self.scheduler, profile_names)
        schedule_layout.addWidget(self.schedule_widget)

        self.tabs.addTab(schedule_tab, "📅 Harmonogram")

        # Tab 3: Ustawienia
        settings_tab = self._build_settings_tab()
        self.tabs.addTab(settings_tab, "⚙️ Ustawienia")

        main_layout.addWidget(self.tabs, 1)

        # ── Pasek statusu ──
        self._build_status_bar()

        # Odśwież karty
        self._refresh_profiles()

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(12)

        # Logo / Tytuł
        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel("🧠 Context Switcher Pro")
        title.setObjectName("titleLabel")
        title_col.addWidget(title)

        subtitle = QLabel("Samo-enforsujący się planer dnia – kontroluj swoje środowisko i przebodźcowanie")
        subtitle.setObjectName("subtitleLabel")
        title_col.addWidget(subtitle)

        header.addLayout(title_col)
        header.addStretch()

        # Aktywny profil badge
        self.active_badge = QLabel("Brak aktywnego profilu")
        self.active_badge.setStyleSheet("""
            QLabel {
                background: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
        """)
        header.addWidget(self.active_badge)

        return header

    def _build_settings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(16)

        # Info o aplikacji
        info_frame = QFrame()
        info_frame.setObjectName("cardFrame")
        info_layout = QVBoxLayout(info_frame)

        info_title = QLabel("ℹ️ O aplikacji")
        info_title.setObjectName("sectionTitle")
        info_layout.addWidget(info_title)

        info_text = QLabel(
            "Context Switcher Pro to samo-enforsujący się planer dnia.\n"
            "Jednym kliknięciem przełącz swoje środowisko między trybami pracy.\n\n"
            "Funkcje:\n"
            "• Zarządzanie profilami (uruchamianie/zamykanie app, głośność, tapeta, motyw, plan zasilania)\n"
            "• Automatyczne przełączanie wg harmonogramu\n"
            "• Monitor przebodźcowania – śledzi co robisz i jak bardzo to Cię stymuluje\n"
            "• Blokowanie rozpraszaczy – wyłącz komunikatory i social media\n\n"
            "Motywacja: Ludzie są przebodźcowani. Chcemy kontrolować\n"
            "przebodźcowanie za pomocą profili i monitoringu aktywności."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.5;")
        info_layout.addWidget(info_text)

        layout.addWidget(info_frame)

        # Sterowania monitorem
        monitor_frame = QFrame()
        monitor_frame.setObjectName("cardFrame")
        monitor_layout = QVBoxLayout(monitor_frame)

        monitor_title = QLabel("🧠 Ustawienia monitora")
        monitor_title.setObjectName("sectionTitle")
        monitor_layout.addWidget(monitor_title)

        # Pokaż korekty
        overrides = self.monitor.get_overrides()
        if overrides:
            for proc, score in overrides.items():
                row = QHBoxLayout()
                lbl = QLabel(f"{proc}: {score}/10")
                lbl.setStyleSheet("color: #94a3b8;")
                row.addWidget(lbl)

                remove_btn = QPushButton("Usuń korektę")
                remove_btn.setStyleSheet("""
                    QPushButton {
                        background: transparent; color: #ef4444;
                        border: 1px solid #ef4444; border-radius: 4px;
                        padding: 4px 8px; font-size: 11px;
                    }
                    QPushButton:hover { background: rgba(239,68,68,0.1); }
                """)
                proc_name = proc
                remove_btn.clicked.connect(
                    lambda checked, p=proc_name: self._remove_override(p)
                )
                row.addWidget(remove_btn)
                row.addStretch()
                monitor_layout.addLayout(row)
        else:
            no_overrides = QLabel("Brak ręcznych korekt – analiza w pełni automatyczna.")
            no_overrides.setStyleSheet("color: #64748b; font-style: italic;")
            monitor_layout.addWidget(no_overrides)

        layout.addWidget(monitor_frame)
        layout.addStretch()

        return tab

    def _build_status_bar(self):
        status_bar = self.statusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background: #111827;
                color: #64748b;
                border-top: 1px solid #1e293b;
                font-size: 11px;
                padding: 4px;
            }
        """)
        status_bar.showMessage("Gotowy – Context Switcher Pro v1.0")

    # ─── System Tray ──────────────────────────────────────────────

    def _setup_tray(self):
        """Skonfiguruj ikonę w zasobniku systemowym."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Context Switcher Pro")

        # Menu zasobnika
        tray_menu = QMenu()

        show_action = QAction("Pokaż okno", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        # Profile w tray menu
        for profile in self.profile_manager.profiles:
            action = QAction(f"{profile.icon} {profile.name}", self)
            name = profile.name
            action.triggered.connect(
                lambda checked, n=name: self.profile_manager.switch_profile(n)
            )
            tray_menu.addAction(action)

        tray_menu.addSeparator()

        deactivate_action = QAction("⏹ Dezaktywuj profil", self)
        deactivate_action.triggered.connect(self.profile_manager.deactivate_profile)
        tray_menu.addAction(deactivate_action)

        tray_menu.addSeparator()

        quit_action = QAction("Zamknij", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    # ─── Odświeżanie profili ──────────────────────────────────────

    def _refresh_profiles(self):
        """Przebuduj karty profili."""
        # Wyczyść
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Dodaj karty
        active_name = (
            self.profile_manager.active_profile.name
            if self.profile_manager.active_profile else None
        )
        for profile in self.profile_manager.profiles:
            card = ProfileCard(
                name=profile.name,
                icon=profile.icon,
                color=profile.color,
                description=profile.description,
                actions_count=len(profile.actions),
                is_active=(profile.name == active_name),
            )
            card.switchClicked.connect(self._on_card_switch)
            card.editClicked.connect(self._on_card_edit)
            card.deleteClicked.connect(self._on_card_delete)
            card.duplicateClicked.connect(self._on_card_duplicate)
            self.cards_layout.addWidget(card)

        # Przycisk dodawania
        add_btn = QPushButton("➕\nNowy profil")
        add_btn.setObjectName("addButton")
        add_btn.setFixedSize(200, 200)
        add_btn.clicked.connect(self._on_add_profile)
        self.cards_layout.addWidget(add_btn)

        self.cards_layout.addStretch()

        # Zaktualizuj schedule widget
        profile_names = [p.name for p in self.profile_manager.profiles]
        if hasattr(self, 'schedule_widget'):
            self.schedule_widget.update_profile_names(profile_names)

    # ─── Handlery kart ────────────────────────────────────────────

    def _on_card_switch(self, name: str):
        """Przełącz lub dezaktywuj profil."""
        if (self.profile_manager.active_profile
                and self.profile_manager.active_profile.name == name):
            self.profile_manager.deactivate_profile()
        else:
            self.profile_manager.switch_profile(name)

    def _on_card_edit(self, name: str):
        profile = self.profile_manager.get_profile(name)
        if not profile:
            return
        dialog = ProfileEditorDialog(profile, self)
        dialog.profileSaved.connect(
            lambda data: self._save_edited_profile(name, data)
        )
        dialog.exec()

    def _on_card_delete(self, name: str):
        reply = QMessageBox.question(
            self,
            "Usuń profil",
            f'Czy na pewno chcesz usunac profil "{name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.profile_manager.delete_profile(name)

    def _on_card_duplicate(self, name: str):
        self.profile_manager.duplicate_profile(name)

    def _on_add_profile(self):
        dialog = ProfileEditorDialog(parent=self)
        dialog.profileSaved.connect(self._save_new_profile)
        dialog.exec()

    def _save_new_profile(self, data: dict):
        profile = Profile.from_dict(data)
        self.profile_manager.add_profile(profile)

    def _save_edited_profile(self, old_name: str, data: dict):
        updated = Profile.from_dict(data)
        self.profile_manager.update_profile(old_name, updated)

    # ─── Sygnały ──────────────────────────────────────────────────

    def _on_profile_changed(self, name: str):
        """Reakcja na zmianę profilu."""
        if name:
            profile = self.profile_manager.get_profile(name)
            if profile:
                self.active_badge.setText(f"{profile.icon} {profile.name}")
                self.active_badge.setStyleSheet(f"""
                    QLabel {{
                        background: {profile.color}22;
                        color: {profile.color};
                        border: 1px solid {profile.color};
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-size: 13px;
                        font-weight: bold;
                    }}
                """)
                self.statusBar().showMessage(
                    f"Przełączono na profil: {profile.icon} {profile.name}"
                )
                # Powiadomienie systemowe
                if self.tray_icon.isSystemTrayAvailable():
                    self.tray_icon.showMessage(
                        "Context Switcher Pro",
                        f"Aktywny profil: {profile.icon} {profile.name}",
                        QSystemTrayIcon.MessageIcon.Information,
                        3000,
                    )
        else:
            self.active_badge.setText("Brak aktywnego profilu")
            self.active_badge.setStyleSheet("""
                QLabel {
                    background: #1e293b;
                    color: #94a3b8;
                    border: 1px solid #334155;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-size: 13px;
                }
            """)
            self.statusBar().showMessage("Profil dezaktywowany – stan przywrócony")

        self._refresh_profiles()

    def _on_schedule_trigger(self, profile_name: str):
        """Harmonogram wywołał przełączenie."""
        self.profile_manager.switch_profile(profile_name)

    def _remove_override(self, process_name: str):
        self.monitor.remove_override(process_name)

    # ─── Zamykanie ────────────────────────────────────────────────

    def closeEvent(self, event):
        """Minimalizuj do zasobnika zamiast zamykania."""
        event.ignore()
        self.hide()
        if self.tray_icon.isSystemTrayAvailable():
            self.tray_icon.showMessage(
                "Context Switcher Pro",
                "Aplikacja działa w tle. Kliknij dwukrotnie ikonę w zasobniku.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
