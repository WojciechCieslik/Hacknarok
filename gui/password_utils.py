"""Password verification dialog helper."""

from PySide6.QtWidgets import QInputDialog, QLineEdit, QMessageBox


def request_profile_password(parent, profile, reason: str = "continue") -> bool:
    """Return True if the profile is unlocked or the user provided the correct password."""
    if not profile or not profile.locked or not profile.password_hash:
        return True

    pw, ok = QInputDialog.getText(
        parent,
        "Password Protected Profile",
        f"Profile '{profile.name}' is password protected.\n"
        f"Enter password to {reason}:",
        QLineEdit.EchoMode.Password,
    )
    if not ok:
        return False
    if profile.verify_password(pw):
        return True
    QMessageBox.warning(
        parent, "Wrong Password", "The password you entered is incorrect."
    )
    return False
