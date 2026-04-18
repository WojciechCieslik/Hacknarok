"""
MainWindow – główne okno aplikacji Context Switcher Pro.

Zawiera karty profili i harmonogram.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QTabWidget,
    QSystemTrayIcon, QMenu, QMessageBox, QSizePolicy,
    QApplication
)

from core.profile_manager import ProfileManager, Profile
from core.scheduler import Scheduler
from gui.password_utils import request_profile_password
from gui.profile_card import ProfileCard, _hex_to_rgba
from gui.profile_editor import ProfileEditorDialog
from gui.schedule_widget import WeeklyCalendarWidget


class MainWindow(QMainWindow):
    """Główne okno Context Switcher Pro."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Context Switcher Pro")
        self.setMinimumSize(900, 700)
        self.resize(1050, 780)

        self.profile_manager = ProfileManager()
        self.scheduler = Scheduler()

        self.profile_manager.profileChanged.connect(self._on_profile_changed)
        self.profile_manager.profilesUpdated.connect(self._refresh_profiles)
        self.scheduler.scheduleTriggered.connect(self._on_schedule_trigger)
        self.scheduler.scheduleEnded.connect(self._on_schedule_end)

        # Timer egzekwowania blokad (co 5s)
        self._block_timer = QTimer(self)
        self._block_timer.setInterval(5000)
        self._block_timer.timeout.connect(self.profile_manager.enforce_blocks)

        self._setup_ui()
        self._setup_tray()

        self.scheduler.start()
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

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.cards_scroll.setStyleSheet("QScrollArea { border: none; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.cards_scroll.setWidget(self.cards_container)
        profiles_layout.addWidget(self.cards_scroll)

        self.tabs.addTab(profiles_tab, "Profile")

        # Tab 2: Harmonogram
        schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(schedule_tab)
        schedule_layout.setContentsMargins(0, 16, 0, 0)

        profile_names = [p.name for p in self.profile_manager.profiles]
        self.schedule_widget = WeeklyCalendarWidget(
            self.scheduler, profile_names, profile_manager=self.profile_manager
        )
        schedule_layout.addWidget(self.schedule_widget)

        self.tabs.addTab(schedule_tab, "Harmonogram")

        # Tab 3: Ustawienia
        settings_tab = self._build_settings_tab()
        self.tabs.addTab(settings_tab, "Ustawienia")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs, 1)

        self._build_status_bar()
        self._refresh_profiles()

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel("Context Switcher Pro")
        title.setObjectName("titleLabel")
        title_col.addWidget(title)

        subtitle = QLabel("Samo-enforsujący się planer dnia – kontroluj swoje środowisko")
        subtitle.setObjectName("subtitleLabel")
        title_col.addWidget(subtitle)

        header.addLayout(title_col)
        header.addStretch()

        self.active_badge = QLabel("-- brak aktywnego profilu --")
        self.active_badge.setStyleSheet("""
            QLabel {
                background: #141414;
                color: #444444;
                border: 1px solid #1e1e1e;
                border-left: 2px solid #2a2a2a;
                padding: 6px 14px;
                font-size: 10px;
                font-family: "JetBrains Mono", "Consolas", monospace;
                letter-spacing: 1px;
            }
        """)
        header.addWidget(self.active_badge)

        return header

    def _build_settings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(16)

        info_frame = QFrame()
        info_frame.setObjectName("cardFrame")
        info_layout = QVBoxLayout(info_frame)

        info_title = QLabel("O aplikacji")
        info_title.setObjectName("sectionTitle")
        info_layout.addWidget(info_title)

        info_text = QLabel(
            "Context Switcher Pro to samo-enforsujący się planer dnia.\n"
            "Jednym kliknięciem przełącz swoje środowisko między trybami pracy.\n\n"
            "Funkcje:\n"
            "• Zarządzanie profilami (tapeta, motyw, uruchamianie/zamykanie aplikacji)\n"
            "• Automatyczne przełączanie wg harmonogramu tygodniowego\n"
            "• Blokowanie rozpraszaczy – wybrane aplikacje będą zamykane gdy profil aktywny"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.5;")
        info_layout.addWidget(info_text)

        layout.addWidget(info_frame)
        layout.addStretch()

        return tab

    def _build_status_bar(self):
        status_bar = self.statusBar()
        status_bar.showMessage("READY  //  Context Switcher Pro v1.0")

    # ─── System Tray (bez powiadomień push) ───────────────────────

    def _setup_tray(self):
        """Tray tylko do szybkiego przełączania profili i wywołania okna."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("Context Switcher Pro")

        tray_menu = QMenu()

        show_action = QAction("Pokaż okno", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        for profile in self.profile_manager.profiles:
            action = QAction(profile.name, self)
            name = profile.name
            action.triggered.connect(
                lambda checked, n=name: self._on_card_switch(n)
            )
            tray_menu.addAction(action)

        tray_menu.addSeparator()

        deactivate_action = QAction("Dezaktywuj profil", self)
        deactivate_action.triggered.connect(self._manual_deactivate)
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
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
                actions=profile.actions,
                blocked_sites=profile.blocked_sites,
                is_active=(profile.name == active_name),
            )
            card.switchClicked.connect(self._on_card_switch)
            card.editClicked.connect(self._on_card_edit)
            card.deleteClicked.connect(self._on_card_delete)
            self.cards_layout.addWidget(card)

        add_btn = QPushButton("+ Nowy profil")
        add_btn.setObjectName("profileAddButton")
        add_btn.setFixedHeight(52)
        add_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        add_btn.clicked.connect(self._on_add_profile)
        self.cards_layout.addWidget(add_btn)

        self.cards_layout.addStretch()

        if hasattr(self, 'schedule_widget'):
            profile_names = [p.name for p in self.profile_manager.profiles]
            colors = {p.name: p.color for p in self.profile_manager.profiles}
            self.schedule_widget.update_profile_names(profile_names)
            self.schedule_widget.update_profile_colors(colors)

    # ─── Handlery kart ────────────────────────────────────────────

    def _on_card_switch(self, name: str):
        """Ręczna aktywacja/dezaktywacja profilu – nadpisuje harmonogram."""
        if (self.profile_manager.active_profile
                and self.profile_manager.active_profile.name == name):
            self._manual_deactivate()
        else:
            profile = self.profile_manager.get_profile(name)
            if profile and not request_profile_password(
                self, profile, "aktywować profil"
            ):
                return
            self.profile_manager.switch_profile(name, manual=True)

    def _manual_deactivate(self):
        """Dezaktywacja ręczna – poinformuj harmonogram aby nie wznawiał bloku."""
        active = self.profile_manager.active_profile
        if active and not request_profile_password(
            self, active, "dezaktywować profil"
        ):
            return
        self.scheduler.notify_manual_deactivation()
        self.profile_manager.deactivate_profile()

    def _on_card_edit(self, name: str):
        profile = self.profile_manager.get_profile(name)
        if not profile:
            return
        if not request_profile_password(self, profile, "edytować profil"):
            return
        dialog = ProfileEditorDialog(profile, self)
        dialog.profileSaved.connect(
            lambda data: self._save_edited_profile(name, data)
        )
        dialog.exec()

    def _on_card_delete(self, name: str):
        profile = self.profile_manager.get_profile(name)
        if profile and not request_profile_password(self, profile, "usunąć profil"):
            return
        reply = QMessageBox.question(
            self,
            "Usuń profil",
            f'Czy na pewno chcesz usunac profil "{name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.profile_manager.delete_profile(name)
            self.scheduler.clear_blocks_for_profile(name)

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
        if name:
            profile = self.profile_manager.get_profile(name)
            if profile:
                self.active_badge.setText(f"[ {profile.name.upper()} ]")
                self.active_badge.setStyleSheet(f"""
                    QLabel {{
                        background: rgba(0, 200, 83, 0.08);
                        color: #00C853;
                        border: 1px solid rgba(0, 200, 83, 0.3);
                        border-left: 2px solid #00C853;
                        padding: 6px 14px;
                        font-size: 10px;
                        font-family: "JetBrains Mono", "Consolas", monospace;
                        font-weight: bold;
                        letter-spacing: 2px;
                    }}
                """)
                self.statusBar().showMessage(
                    f"AKTYWNY: {profile.name.upper()}"
                )
        else:
            self.active_badge.setText("-- brak aktywnego profilu --")
            self.active_badge.setStyleSheet("""
                QLabel {
                    background: #141414;
                    color: #444444;
                    border: 1px solid #1e1e1e;
                    border-left: 2px solid #2a2a2a;
                    padding: 6px 14px;
                    font-size: 10px;
                    font-family: "JetBrains Mono", "Consolas", monospace;
                    letter-spacing: 1px;
                }
            """)
            self.statusBar().showMessage("DEZAKTYWOWANY -- stan przywrocony")

        self._refresh_profiles()

    def _on_tab_changed(self, index: int):
        if hasattr(self, "schedule_widget") and index == 1:
            self.schedule_widget.scroll_to_now()

    def _on_schedule_trigger(self, profile_name: str):
        """Harmonogram rozpoczął blok – aktywuj profil (jeśli nie ma ręcznego override)."""
        if self.profile_manager.manual_override:
            return
        self.profile_manager.switch_profile(profile_name, manual=False)

    def _on_schedule_end(self, _unused: str):
        """Harmonogram zakończył blok – dezaktywuj profil jeśli wciąż nasz."""
        if self.profile_manager.manual_override:
            return
        if self.profile_manager.active_profile:
            self.profile_manager.deactivate_profile()
