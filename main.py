"""
Context Switcher Pro – Punkt wejścia aplikacji.

Samo-enforsujący się planer dnia – kontroluj swoje środowisko i przebodźcowanie.
Jednym kliknięciem przełącz się między „Praca", „Nauka", „Rozrywka".
"""

import sys
import os
import logging
import threading

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ContextSwitcherPro")

# Dodaj katalog projektu do ścieżki
_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)


def _start_extension_server():
    """Uruchamia serwer Flask dla rozszerzenia Chrome w tle."""
    try:
        sys.path.insert(0, os.path.join(_ROOT, "extension"))
        from server import app
        import logging as _log
        _log.getLogger("werkzeug").setLevel(_log.WARNING)
        app.run(port=8765, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Błąd serwera rozszerzenia: {e}")


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

    # Serwer rozszerzenia Chrome (daemon – ginie razem z aplikacją)
    server_thread = threading.Thread(target=_start_extension_server, daemon=True)
    server_thread.start()
    logger.info("Serwer rozszerzenia uruchomiony na porcie 8765")

    # Główne okno
    window = MainWindow()
    window.show()

    logger.info("Context Switcher Pro uruchomiony")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
