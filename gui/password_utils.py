"""Pomocnik: weryfikacja hasła profilu przez dialog."""

from PySide6.QtWidgets import QInputDialog, QLineEdit, QMessageBox


def request_profile_password(parent, profile, reason: str = "kontynuować") -> bool:
    """Zwróć True jeśli profil jest odblokowany lub użytkownik podał poprawne hasło."""
    if not profile or not profile.locked or not profile.password_hash:
        return True

    pw, ok = QInputDialog.getText(
        parent,
        "Profil chroniony hasłem",
        f"Profil '{profile.name}' jest chroniony hasłem.\n"
        f"Wpisz hasło aby {reason}:",
        QLineEdit.EchoMode.Password,
    )
    if not ok:
        return False
    if profile.verify_password(pw):
        return True
    QMessageBox.warning(
        parent, "Błędne hasło", "Podane hasło jest nieprawidłowe."
    )
    return False