"""
Styles – industrial blueprint theme dopasowany do logo (kobalt + chrom).
"""

COLORS = {
    "bg_void":      "#070a1f",
    "bg_base":      "#0d1230",
    "bg_panel":     "#141a44",
    "bg_panel_hi":  "#1b2458",
    "bg_input":     "#0f1538",
    "bg_surface":   "#171f4e",

    "line":         "#2a3372",
    "line_bright":  "#4856b5",
    "line_hot":     "#6d7fff",

    "chrome":       "#e8ecf5",
    "chrome_dim":   "#aab3d8",
    "chrome_mute":  "#727aa3",

    "indigo":       "#5968ff",
    "indigo_hot":   "#7d8aff",
    "indigo_deep":  "#3a47d4",
    "cobalt":       "#2b3dd1",

    "accent":       "#5968ff",
    "accent_hover": "#7d8aff",

    "warn":         "#d89b3a",
    "danger":       "#e5484d",
    "danger_deep":  "#b83238",
    "ok":           "#3fb98a",

    "text":         "#e8ecf5",
    "text_dim":     "#aab3d8",
    "text_mute":    "#727aa3",
    "text_faint":   "#4a5186",
}


MAIN_STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {COLORS["bg_void"]};
    color: {COLORS["text"]};
}}

QWidget {{
    color: {COLORS["text"]};
    font-family: "Inter", "IBM Plex Sans", "Segoe UI", sans-serif;
    font-size: 13px;
}}

QWidget#centralWidget {{
    background-color: {COLORS["bg_void"]};
}}

QLabel {{
    color: {COLORS["text"]};
    background: transparent;
}}

QLabel#titleLabel {{
    font-family: "JetBrains Mono", "IBM Plex Mono", "Fira Code", "Consolas", monospace;
    font-size: 20px;
    font-weight: 700;
    color: {COLORS["chrome"]};
    letter-spacing: 3px;
}}

QLabel#subtitleLabel {{
    font-family: "JetBrains Mono", "IBM Plex Mono", "Consolas", monospace;
    font-size: 11px;
    color: {COLORS["text_mute"]};
    letter-spacing: 2px;
}}

QLabel#sectionTitle {{
    font-family: "JetBrains Mono", "IBM Plex Mono", "Consolas", monospace;
    font-size: 11px;
    font-weight: 700;
    color: {COLORS["chrome_dim"]};
    letter-spacing: 3px;
    padding: 4px 0 8px 0;
    border-bottom: 1px solid {COLORS["line"]};
}}

QLabel#brandMark {{
    font-family: "JetBrains Mono", "Consolas", monospace;
    color: {COLORS["chrome"]};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    border: 1px solid {COLORS["line_bright"]};
    background: {COLORS["bg_panel"]};
    padding: 4px 8px;
}}

QPushButton {{
    background-color: {COLORS["bg_panel"]};
    color: {COLORS["chrome"]};
    border: 1px solid {COLORS["line_bright"]};
    border-radius: 2px;
    padding: 9px 18px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    min-height: 18px;
}}

QPushButton:hover {{
    background-color: {COLORS["bg_panel_hi"]};
    border-color: {COLORS["indigo_hot"]};
    color: {COLORS["chrome"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["indigo_deep"]};
    border-color: {COLORS["indigo_hot"]};
}}

QPushButton:disabled {{
    color: {COLORS["text_faint"]};
    border-color: {COLORS["line"]};
    background-color: {COLORS["bg_base"]};
}}

QPushButton#primaryButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS["cobalt"]}, stop:1 {COLORS["indigo"]});
    border: 1px solid {COLORS["indigo_hot"]};
    color: {COLORS["chrome"]};
    padding: 11px 26px;
    font-weight: 700;
}}

QPushButton#primaryButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS["indigo_deep"]}, stop:1 {COLORS["indigo_hot"]});
}}

QPushButton#dangerButton {{
    background-color: {COLORS["bg_panel"]};
    border: 1px solid {COLORS["danger"]};
    color: {COLORS["danger"]};
}}

QPushButton#dangerButton:hover {{
    background-color: {COLORS["danger"]};
    color: {COLORS["chrome"]};
}}

QPushButton#switchButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS["cobalt"]}, stop:1 {COLORS["indigo_hot"]});
    border: 1px solid {COLORS["indigo_hot"]};
    color: {COLORS["chrome"]};
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 12px 26px;
    min-height: 26px;
}}

QPushButton#switchButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {COLORS["indigo"]}, stop:1 #9fabff);
}}

QPushButton#deactivateButton {{
    background: {COLORS["bg_panel"]};
    border: 1px solid {COLORS["warn"]};
    color: {COLORS["warn"]};
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 12px 26px;
    min-height: 26px;
}}

QPushButton#deactivateButton:hover {{
    background: {COLORS["warn"]};
    color: {COLORS["bg_void"]};
}}

QLineEdit, QTextEdit, QSpinBox {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["chrome"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 2px;
    padding: 9px 12px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 12px;
    selection-background-color: {COLORS["indigo"]};
}}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {{
    border: 1px solid {COLORS["indigo_hot"]};
    background-color: {COLORS["bg_surface"]};
}}

QComboBox {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["chrome"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 2px;
    padding: 8px 12px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 12px;
    min-height: 20px;
    letter-spacing: 1px;
}}

QComboBox:hover {{
    border-color: {COLORS["indigo_hot"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
    border-left: 1px solid {COLORS["line"]};
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLORS["chrome_dim"]};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_panel"]};
    color: {COLORS["chrome"]};
    border: 1px solid {COLORS["line_bright"]};
    border-radius: 0;
    selection-background-color: {COLORS["indigo_deep"]};
    outline: none;
    padding: 2px;
}}

QSlider::groove:horizontal {{
    background: {COLORS["bg_input"]};
    height: 4px;
    border: 1px solid {COLORS["line"]};
}}

QSlider::handle:horizontal {{
    background: {COLORS["chrome"]};
    border: 1px solid {COLORS["indigo"]};
    width: 12px;
    height: 14px;
    margin: -6px 0;
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS["indigo_hot"]};
}}

QSlider::sub-page:horizontal {{
    background: {COLORS["indigo"]};
}}

QCheckBox {{
    color: {COLORS["text"]};
    spacing: 10px;
    font-size: 12px;
    font-family: "Inter", "Segoe UI", sans-serif;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS["line_bright"]};
    border-radius: 0;
    background: {COLORS["bg_input"]};
}}

QCheckBox::indicator:checked {{
    background: {COLORS["indigo"]};
    border: 1px solid {COLORS["indigo_hot"]};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS["indigo_hot"]};
}}

QGroupBox {{
    background-color: {COLORS["bg_panel"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 0;
    margin-top: 14px;
    padding: 18px 14px 14px 14px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    color: {COLORS["chrome_dim"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    background: {COLORS["bg_void"]};
}}

QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

QScrollBar:vertical {{
    background: {COLORS["bg_base"]};
    width: 6px;
    border: none;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["line_bright"]};
    border-radius: 0;
    min-height: 24px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["indigo_hot"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {COLORS["bg_base"]};
    height: 6px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS["line_bright"]};
    min-width: 24px;
}}

QTabWidget::pane {{
    background: {COLORS["bg_void"]};
    border: 1px solid {COLORS["line"]};
    border-top: none;
    border-radius: 0;
}}

QTabBar {{
    qproperty-drawBase: 0;
    background: transparent;
}}

QTabBar::tab {{
    background: transparent;
    color: {COLORS["text_mute"]};
    border: none;
    border-bottom: 1px solid {COLORS["line"]};
    padding: 12px 24px;
    margin-right: 0;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
}}

QTabBar::tab:selected {{
    color: {COLORS["chrome"]};
    border-bottom: 2px solid {COLORS["indigo_hot"]};
}}

QTabBar::tab:hover:!selected {{
    color: {COLORS["chrome_dim"]};
    border-bottom-color: {COLORS["line_bright"]};
}}

QMenu {{
    background-color: {COLORS["bg_panel"]};
    color: {COLORS["chrome"]};
    border: 1px solid {COLORS["line_bright"]};
    border-radius: 0;
    padding: 2px;
}}

QMenu::item {{
    padding: 8px 22px;
    border-radius: 0;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 11px;
    letter-spacing: 1px;
}}

QMenu::item:selected {{
    background-color: {COLORS["indigo_deep"]};
}}

QMenu::separator {{
    height: 1px;
    background: {COLORS["line"]};
    margin: 4px 0;
}}

QListWidget {{
    background-color: {COLORS["bg_panel"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 0;
    padding: 2px;
    outline: none;
}}

QListWidget::item {{
    padding: 10px;
    border-radius: 0;
    margin: 1px;
}}

QListWidget::item:selected {{
    background-color: {COLORS["indigo_deep"]};
    color: {COLORS["chrome"]};
}}

QListWidget::item:hover:!selected {{
    background-color: {COLORS["bg_panel_hi"]};
}}

QProgressBar {{
    background-color: {COLORS["bg_input"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 0;
    height: 8px;
    text-align: center;
    font-size: 10px;
    color: {COLORS["chrome"]};
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS["cobalt"]}, stop:1 {COLORS["indigo_hot"]});
}}

QToolTip {{
    background-color: {COLORS["bg_panel"]};
    color: {COLORS["chrome"]};
    border: 1px solid {COLORS["line_bright"]};
    border-radius: 0;
    padding: 6px 10px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 11px;
}}

QFrame#cardFrame {{
    background-color: {COLORS["bg_panel"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 0;
}}

QFrame#activeCardFrame {{
    background-color: {COLORS["bg_panel"]};
    border: 1px solid {COLORS["indigo_hot"]};
    border-left: 3px solid {COLORS["indigo_hot"]};
    border-radius: 0;
}}

QPushButton#profileAddButton {{
    background: transparent;
    border: 1px dashed {COLORS["line_bright"]};
    color: {COLORS["chrome_dim"]};
    border-radius: 0;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
    text-align: center;
    padding: 14px;
}}

QPushButton#profileAddButton:hover {{
    border: 1px solid {COLORS["indigo_hot"]};
    border-style: solid;
    color: {COLORS["chrome"]};
    background: {COLORS["bg_panel"]};
}}

QFrame#overloadFrame {{
    background-color: {COLORS["bg_panel"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 0;
    padding: 14px;
}}

QFrame#separator {{
    background-color: {COLORS["line"]};
    max-height: 1px;
}}

QFrame#headerRule {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS["line_hot"]}, stop:0.2 {COLORS["line_bright"]},
        stop:1 transparent);
    max-height: 1px;
}}

QStatusBar {{
    background: {COLORS["bg_base"]};
    color: {COLORS["text_mute"]};
    border-top: 1px solid {COLORS["line"]};
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 10px;
    letter-spacing: 1.5px;
    padding: 4px;
}}
"""
