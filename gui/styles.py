"""
Styles – styl QSS dla Context Switcher Pro.

Ciemny motyw premium z glassmorphizmem, gradientami i animacjami.
"""

# ─── Paleta kolorów ──────────────────────────────────────────────

COLORS = {
    "bg_primary": "#0a0e1a",
    "bg_secondary": "#111827",
    "bg_card": "#1e293b",
    "bg_card_hover": "#273548",
    "bg_input": "#1a2332",
    "bg_surface": "rgba(30, 41, 59, 0.85)",

    "accent_purple": "#7c3aed",
    "accent_purple_hover": "#8b5cf6",
    "accent_cyan": "#06b6d4",
    "accent_green": "#10b981",
    "accent_yellow": "#f59e0b",
    "accent_orange": "#f97316",
    "accent_red": "#ef4444",
    "accent_red_dark": "#dc2626",

    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",

    "border": "#334155",
    "border_focus": "#7c3aed",

    "shadow": "rgba(0, 0, 0, 0.3)",
}


# ─── Główny styl QSS ────────────────────────────────────────────

MAIN_STYLESHEET = f"""
/* ── Globalnie ─────────────────────────────────────────────── */
QMainWindow {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
}}

QWidget {{
    color: {COLORS["text_primary"]};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}}

QWidget#centralWidget {{
    background-color: {COLORS["bg_primary"]};
}}

/* ── Etykiety ──────────────────────────────────────────────── */
QLabel {{
    color: {COLORS["text_primary"]};
    background: transparent;
    padding: 0px;
}}

QLabel#titleLabel {{
    font-size: 22px;
    font-weight: bold;
    color: {COLORS["text_primary"]};
}}

QLabel#subtitleLabel {{
    font-size: 14px;
    color: {COLORS["text_secondary"]};
}}

QLabel#sectionTitle {{
    font-size: 16px;
    font-weight: bold;
    color: {COLORS["text_primary"]};
    padding: 8px 0px;
}}

QLabel#activeWindowLabel {{
    font-size: 12px;
    color: {COLORS["text_secondary"]};
    padding: 4px 8px;
    background: {COLORS["bg_card"]};
    border-radius: 6px;
}}

/* ── Przyciski ─────────────────────────────────────────────── */
QPushButton {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS["bg_card_hover"]};
    border-color: {COLORS["accent_purple"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["accent_purple"]};
}}

QPushButton#primaryButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS["accent_purple"]}, stop:1 {COLORS["accent_cyan"]});
    border: none;
    color: white;
    font-weight: bold;
    padding: 12px 28px;
    font-size: 14px;
}}

QPushButton#primaryButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS["accent_purple_hover"]}, stop:1 #22d3ee);
}}

QPushButton#dangerButton {{
    background-color: {COLORS["accent_red"]};
    border: none;
    color: white;
}}

QPushButton#dangerButton:hover {{
    background-color: {COLORS["accent_red_dark"]};
}}

QPushButton#switchButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS["accent_purple"]}, stop:1 {COLORS["accent_cyan"]});
    border: none;
    color: white;
    font-size: 15px;
    font-weight: bold;
    padding: 14px 32px;
    border-radius: 12px;
    min-height: 30px;
}}

QPushButton#switchButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS["accent_purple_hover"]}, stop:1 #22d3ee);
}}

QPushButton#deactivateButton {{
    background-color: {COLORS["accent_orange"]};
    border: none;
    color: white;
    font-weight: bold;
    padding: 14px 32px;
    border-radius: 12px;
    font-size: 15px;
    min-height: 30px;
}}

QPushButton#deactivateButton:hover {{
    background-color: #ea580c;
}}

QPushButton#addButton {{
    background: transparent;
    border: 2px dashed {COLORS["border"]};
    color: {COLORS["text_muted"]};
    border-radius: 12px;
    font-size: 28px;
    min-height: 100px;
}}

QPushButton#addButton:hover {{
    border-color: {COLORS["accent_purple"]};
    color: {COLORS["accent_purple"]};
    background: rgba(124, 58, 237, 0.05);
}}

/* ── Pola tekstowe ─────────────────────────────────────────── */
QLineEdit {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    selection-background-color: {COLORS["accent_purple"]};
}}

QLineEdit:focus {{
    border-color: {COLORS["border_focus"]};
}}

QTextEdit {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
}}

QTextEdit:focus {{
    border-color: {COLORS["border_focus"]};
}}

/* ── Rozwijane listy ───────────────────────────────────────── */
QComboBox {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
}}

QComboBox:hover {{
    border-color: {COLORS["accent_purple"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS["text_secondary"]};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    selection-background-color: {COLORS["accent_purple"]};
    padding: 4px;
}}

/* ── Slider ────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    background: {COLORS["bg_input"]};
    height: 8px;
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: {COLORS["accent_purple"]};
    width: 20px;
    height: 20px;
    margin: -6px 0;
    border-radius: 10px;
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS["accent_purple_hover"]};
}}

QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS["accent_purple"]}, stop:1 {COLORS["accent_cyan"]});
    border-radius: 4px;
}}

/* ── SpinBox ───────────────────────────────────────────────── */
QSpinBox {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
}}

QSpinBox:focus {{
    border-color: {COLORS["border_focus"]};
}}

/* ── CheckBox ──────────────────────────────────────────────── */
QCheckBox {{
    color: {COLORS["text_primary"]};
    spacing: 8px;
    font-size: 13px;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {COLORS["border"]};
    border-radius: 4px;
    background: {COLORS["bg_input"]};
}}

QCheckBox::indicator:checked {{
    background: {COLORS["accent_purple"]};
    border-color: {COLORS["accent_purple"]};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS["accent_purple"]};
}}

/* ── Grupa ─────────────────────────────────────────────────── */
QGroupBox {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    margin-top: 16px;
    padding: 20px 16px 16px 16px;
    font-size: 14px;
    font-weight: bold;
    color: {COLORS["text_primary"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
}}

/* ── ScrollArea ────────────────────────────────────────────── */
QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

QScrollBar:vertical {{
    background: {COLORS["bg_secondary"]};
    width: 8px;
    border-radius: 4px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["border"]};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["text_muted"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {COLORS["bg_secondary"]};
    height: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS["border"]};
    border-radius: 4px;
    min-width: 30px;
}}

/* ── TabWidget ─────────────────────────────────────────────── */
QTabWidget::pane {{
    background: {COLORS["bg_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 0 0 12px 12px;
    border-top: none;
}}

QTabBar::tab {{
    background: {COLORS["bg_card"]};
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border"]};
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    padding: 10px 20px;
    margin-right: 2px;
    font-size: 13px;
}}

QTabBar::tab:selected {{
    background: {COLORS["bg_primary"]};
    color: {COLORS["accent_purple"]};
    font-weight: bold;
    border-bottom: 2px solid {COLORS["accent_purple"]};
}}

QTabBar::tab:hover:!selected {{
    background: {COLORS["bg_card_hover"]};
    color: {COLORS["text_primary"]};
}}

/* ── Dialog ────────────────────────────────────────────────── */
QDialog {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
}}

/* ── Menu ──────────────────────────────────────────────────── */
QMenu {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS["accent_purple"]};
}}

/* ── Lista ─────────────────────────────────────────────────── */
QListWidget {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}

QListWidget::item {{
    padding: 10px;
    border-radius: 6px;
    margin: 2px;
}}

QListWidget::item:selected {{
    background-color: {COLORS["accent_purple"]};
    color: white;
}}

QListWidget::item:hover:!selected {{
    background-color: {COLORS["bg_card_hover"]};
}}

/* ── Progress Bar ──────────────────────────────────────────── */
QProgressBar {{
    background-color: {COLORS["bg_input"]};
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    font-size: 10px;
    color: white;
}}

QProgressBar::chunk {{
    border-radius: 6px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS["accent_green"]}, stop:0.5 {COLORS["accent_yellow"]},
        stop:0.8 {COLORS["accent_orange"]}, stop:1 {COLORS["accent_red"]});
}}

/* ── ToolTip ───────────────────────────────────────────────── */
QToolTip {{
    background-color: {COLORS["bg_card"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ── Customowe klasy ───────────────────────────────────────── */
QFrame#cardFrame {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
}}

QFrame#activeCardFrame {{
    background-color: {COLORS["bg_card"]};
    border: 2px solid {COLORS["accent_purple"]};
    border-radius: 12px;
}}

QPushButton#profileAddButton {{
    background: transparent;
    border: 2px dashed {COLORS["border"]};
    color: {COLORS["text_muted"]};
    border-radius: 10px;
    font-size: 14px;
    font-weight: 500;
    text-align: left;
    padding-left: 16px;
}}

QPushButton#profileAddButton:hover {{
    border-color: {COLORS["accent_purple"]};
    color: {COLORS["accent_purple"]};
    background: rgba(124, 58, 237, 0.05);
}}

QFrame#overloadFrame {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 16px;
}}

QFrame#separator {{
    background-color: {COLORS["border"]};
    max-height: 1px;
}}
"""
