"""
Context Switcher Pro – Punkt wejścia aplikacji.

Samo-enforsujący się planer dnia – kontroluj swoje środowisko i przebodźcowanie.
Jednym kliknięciem przełącz się między „Praca", „Nauka", „Rozrywka".
"""

import sys
import os
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ContextSwitcherPro")

# Dodaj katalog projektu do ścieżki
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont
    from gui.main_window import MainWindow
    from gui.styles import MAIN_STYLESHEET

    app = QApplication(sys.argv)
    app.setApplicationName("Context Switcher Pro")
    app.setOrganizationName("ContextSwitcherPro")
    app.setApplicationDisplayName("Context Switcher Pro")

    # Czcionka domyślna
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Styl
    app.setStyleSheet(MAIN_STYLESHEET)

    # Główne okno
    window = MainWindow()
    window.show()

    logger.info("Context Switcher Pro uruchomiony")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
