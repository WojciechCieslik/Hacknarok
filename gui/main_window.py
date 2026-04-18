"""
MainWindow – industrialny panel kontrolny Context Switcher Pro.
"""

import os

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QTabWidget,
    QSystemTrayIcon, QMenu, QMessageBox, QSizePolicy,
    QApplication
)

from core.profile_manager import ProfileManager, Profile
from core.scheduler import Scheduler
from gui.profile_card import ProfileCard, _hex_to_rgba
from gui.profile_editor import ProfileEditorDialog
from gui.schedule_widget import WeeklyCalendarWidget
from gui.styles import COLORS


_ICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.png"
)


class MainWindow(QMainWindow):
    """Główne okno Context Switcher Pro."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CONTEXT SWITCHER // PRO")
        self.setMinimumSize(960, 720)
        self.resize(1080, 800)
        if os.path.exists(_ICON_PATH):
            self.setWindowIcon(QIcon(_ICON_PATH))

        self.profile_manager = ProfileManager()
        self.scheduler = Scheduler()

        self.profile_manager.profileChanged.connect(self._on_profile_changed)
        self.profile_manager.profilesUpdated.connect(self._refresh_profiles)
        self.scheduler.scheduleTriggered.connect(self._on_schedule_trigger)
        self.scheduler.scheduleEnded.connect(self._on_schedule_end)

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
        main_layout.setContentsMargins(28, 22, 28, 16)
        main_layout.setSpacing(14)

        main_layout.addLayout(self._build_header())

        rule = QFrame()
        rule.setObjectName("headerRule")
        rule.setFrameShape(QFrame.Shape.HLine)
        rule.setFixedHeight(1)
        main_layout.addWidget(rule)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        profiles_tab = QWidget()
        profiles_layout = QVBoxLayout(profiles_tab)
        profiles_layout.setContentsMargins(0, 18, 0, 0)

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.cards_scroll.setStyleSheet("QScrollArea { border: none; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.cards_scroll.setWidget(self.cards_container)
        profiles_layout.addWidget(self.cards_scroll)

        self.tabs.addTab(profiles_tab, "01  //  PROFILES")

        schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(schedule_tab)
        schedule_layout.setContentsMargins(0, 18, 0, 0)

        profile_names = [p.name for p in self.profile_manager.profiles]
        self.schedule_widget = WeeklyCalendarWidget(self.scheduler, profile_names)
        schedule_layout.addWidget(self.schedule_widget)

        self.tabs.addTab(schedule_tab, "02  //  SCHEDULE")

        self.tabs.addTab(self._build_settings_tab(), "03  //  SYSTEM")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs, 1)

        self._build_status_bar()
        self._refresh_profiles()

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(16)

        if os.path.exists(_ICON_PATH):
            logo_lbl = QLabel()
            pm = QPixmap(_ICON_PATH).scaled(
                52, 52,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_lbl.setPixmap(pm)
            logo_lbl.setFixedSize(QSize(52, 52))
            logo_lbl.setStyleSheet("background: transparent;")
            header.addWidget(logo_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title = QLabel("CONTEXT  SWITCHER")
        title.setObjectName("titleLabel")
        title_col.addWidget(title)

        subtitle = QLabel("SELF-ENFORCING  ENVIRONMENT  CONTROL  UNIT")
        subtitle.setObjectName("subtitleLabel")
        title_col.addWidget(subtitle)

        header.addLayout(title_col)
        header.addStretch()

        version = QLabel("PRO  ·  v1.0")
        version.setObjectName("brandMark")
        header.addWidget(version, 0, Qt.AlignmentFlag.AlignVCenter)

        self.active_badge = QLabel("IDLE")
        self._set_badge_idle()
        header.addWidget(self.active_badge, 0, Qt.AlignmentFlag.AlignVCenter)

        return header

    def _set_badge_idle(self):
        self.active_badge.setText("STATUS  //  IDLE")
        self.active_badge.setStyleSheet(f"""
            QLabel {{
                background: {COLORS["bg_panel"]};
                color: {COLORS["chrome_mute"]};
                border: 1px solid {COLORS["line"]};
                border-radius: 0;
                padding: 7px 14px;
                font-family: "JetBrains Mono", "Consolas", monospace;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 2px;
            }}
        """)

    def _build_settings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 18, 0, 0)
        layout.setSpacing(16)

        info_frame = QFrame()
        info_frame.setObjectName("cardFrame")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(22, 18, 22, 20)
        info_layout.setSpacing(12)

        info_title = QLabel("SYSTEM  //  DOCUMENTATION")
        info_title.setObjectName("sectionTitle")
        info_layout.addWidget(info_title)

        info_text = QLabel(
            "Context Switcher Pro is a self-enforcing daily planner.\n"
            "One actuation switches the entire environment between operating modes.\n\n"
            "FEATURES\n"
            "   -  Profile management (wallpaper, theme, app launch / termination)\n"
            "   -  Weekly schedule with automatic activation\n"
            "   -  Distraction containment – blocked apps close on contact\n"
            "   -  Website filtering via Chrome extension\n"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(
            f"color: {COLORS['text_dim']};"
            f"font-family: 'JetBrains Mono','Consolas',monospace;"
            f"font-size: 11px; line-height: 1.7; letter-spacing: 0.5px;"
        )
        info_layout.addWidget(info_text)

        layout.addWidget(info_frame)
        layout.addStretch()

        return tab

    def _build_status_bar(self):
        status_bar = self.statusBar()
        status_bar.showMessage("READY  //  CONTEXT SWITCHER PRO  //  v1.0")

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(_ICON_PATH):
            self.tray_icon.setIcon(QIcon(_ICON_PATH))
        self.tray_icon.setToolTip("Context Switcher Pro")

        tray_menu = QMenu()

        show_action = QAction("OPEN  CONSOLE", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        for profile in self.profile_manager.profiles:
            action = QAction(f"ACTIVATE  //  {profile.name.upper()}", self)
            name = profile.name
            action.triggered.connect(
                lambda checked, n=name: self.profile_manager.switch_profile(n, manual=True)
            )
            tray_menu.addAction(action)

        tray_menu.addSeparator()

        deactivate_action = QAction("DEACTIVATE  PROFILE", self)
        deactivate_action.triggered.connect(self._manual_deactivate)
        tray_menu.addAction(deactivate_action)

        tray_menu.addSeparator()

        quit_action = QAction("SHUT  DOWN", self)
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

        add_btn = QPushButton("+   NEW  PROFILE")
        add_btn.setObjectName("profileAddButton")
        add_btn.setFixedHeight(54)
        add_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        add_btn.clicked.connect(self._on_add_profile)
        self.cards_layout.addWidget(add_btn)

        self.cards_layout.addStretch()

        if hasattr(self, 'schedule_widget'):
            profile_names = [p.name for p in self.profile_manager.profiles]
            colors = {p.name: p.color for p in self.profile_manager.profiles}
            self.schedule_widget.update_profile_names(profile_names)
            self.schedule_widget.update_profile_colors(colors)

    def _on_card_switch(self, name: str):
        if (self.profile_manager.active_profile
                and self.profile_manager.active_profile.name == name):
            self._manual_deactivate()
        else:
            self.profile_manager.switch_profile(name, manual=True)

    def _manual_deactivate(self):
        self.scheduler.notify_manual_deactivation()
        self.profile_manager.deactivate_profile()

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
            "REMOVE  PROFILE",
            f'Confirm removal of profile "{name}"?',
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

    def _on_profile_changed(self, name: str):
        if name:
            profile = self.profile_manager.get_profile(name)
            if profile:
                self.active_badge.setText(f"ACTIVE  //  {profile.name.upper()}")
                bg = _hex_to_rgba(profile.color, 48)
                border = _hex_to_rgba(profile.color, 220)
                self.active_badge.setStyleSheet(f"""
                    QLabel {{
                        background: {bg};
                        color: {profile.color};
                        border: 1px solid {border};
                        border-left: 3px solid {profile.color};
                        border-radius: 0;
                        padding: 7px 14px;
                        font-family: "JetBrains Mono", "Consolas", monospace;
                        font-size: 11px;
                        font-weight: 700;
                        letter-spacing: 2px;
                    }}
                """)
                self.statusBar().showMessage(
                    f"SWITCHED  //  PROFILE  :  {profile.name.upper()}"
                )
        else:
            self._set_badge_idle()
            self.statusBar().showMessage("DEACTIVATED  //  STATE  RESTORED")

        self._refresh_profiles()

    def _on_tab_changed(self, index: int):
        if hasattr(self, "schedule_widget") and index == 1:
            self.schedule_widget.scroll_to_now()

    def _on_schedule_trigger(self, profile_name: str):
        if self.profile_manager.manual_override:
            return
        self.profile_manager.switch_profile(profile_name, manual=False)

    def _on_schedule_end(self, _unused: str):
        if self.profile_manager.manual_override:
            return
        if self.profile_manager.active_profile:
            self.profile_manager.deactivate_profile()
