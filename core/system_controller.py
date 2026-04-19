"""
SystemController – wrapper na Windows API.

Hermetyzuje wszystkie wywołania systemowe:
tapeta, motyw, procesy, aktywne okno.
"""

import ctypes
import os
import subprocess
import winreg
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class SystemController:
    """Kontroler systemowy – enkapsuluje wywołania Windows API."""

    # ─── Tapeta ─────────────────────────────────────────────────

    @staticmethod
    def get_wallpaper() -> str:
        """Pobierz ścieżkę aktualnej tapety."""
        try:
            SPI_GETDESKWALLPAPER = 0x0073
            buf = ctypes.create_unicode_buffer(512)
            ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETDESKWALLPAPER, len(buf), buf, 0
            )
            return buf.value
        except Exception as e:
            logger.error(f"Nie udało się pobrać tapety: {e}")
            return ""

    @staticmethod
    def set_wallpaper(image_path: str) -> bool:
        """Zmień tapetę pulpitu."""
        try:
            if not os.path.isfile(image_path):
                logger.error(f"Plik tapety nie istnieje: {image_path}")
                return False
            SPI_SETDESKWALLPAPER = 0x0014
            SPIF_UPDATEINIFILE = 0x01
            SPIF_SENDWININICHANGE = 0x02
            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, image_path,
                SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
            )
            if result:
                logger.info(f"Tapeta zmieniona na: {image_path}")
            return bool(result)
        except Exception as e:
            logger.error(f"Nie udało się zmienić tapety: {e}")
            return False

    # ─── Motyw ciemny/jasny ─────────────────────────────────────

    @staticmethod
    def get_theme() -> bool:
        """Zwraca True jeśli aktywny jest motyw ciemny."""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0  # 0 = ciemny, 1 = jasny
        except Exception as e:
            logger.error(f"Nie udało się odczytać motywu: {e}")
            return False

    @staticmethod
    def set_theme(dark: bool) -> bool:
        """Ustaw motyw ciemny (True) lub jasny (False)."""
        try:
            value = 0 if dark else 1
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, value)
                winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, value)
            logger.info(f"Motyw ustawiony na: {'ciemny' if dark else 'jasny'}")
            return True
        except Exception as e:
            logger.error(f"Nie udało się zmienić motywu: {e}")
            return False

    # ─── Procesy / Aplikacje ────────────────────────────────────

    @staticmethod
    def _resolve_exe(path: str) -> str | None:
        """Rozwiąż nazwę exe na pełną ścieżkę przez PATH i rejestr App Paths."""
        import shutil
        import winreg

        if os.path.isabs(path) and os.path.isfile(path):
            return path

        found = shutil.which(path)
        if found:
            return found

        exe_name = os.path.basename(path)
        reg_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\\" + exe_name
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(hive, reg_key) as k:
                    reg_path, _ = winreg.QueryValueEx(k, "")
                    if reg_path and os.path.isfile(reg_path):
                        return reg_path
            except OSError:
                pass

        return None

    @staticmethod
    def launch_app(path: str, args: list[str] = None) -> bool:
        """Uruchom aplikację. Rozwiązuje nazwę exe przez PATH i rejestr."""
        resolved = SystemController._resolve_exe(path)
        if resolved:
            try:
                subprocess.Popen(
                    [resolved] + (args or []),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                )
                logger.info(f"Uruchomiono: {resolved}")
                return True
            except Exception as e:
                logger.error(f"Nie udało się uruchomić {resolved}: {e}")

        # Fallback: ShellExecute przez shell=True (używa rejestru App Paths)
        try:
            subprocess.Popen(
                path if not args else f'"{path}" ' + " ".join(args),
                shell=True,
            )
            logger.info(f"Uruchomiono (shell): {path}")
            return True
        except Exception as e:
            logger.error(f"Nie udało się uruchomić {path}: {e}")
            return False

    @staticmethod
    def _close_windows_for_pid(pid: int) -> bool:
        """Wyślij WM_CLOSE do wszystkich widocznych okien procesu. Zwraca czy coś zamknięto."""
        try:
            import win32gui
            import win32process
            import win32con

            closed = False

            def _enum(hwnd, _):
                nonlocal closed
                try:
                    _, owner_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if owner_pid == pid and win32gui.IsWindowVisible(hwnd):
                        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                        closed = True
                except Exception:
                    pass

            win32gui.EnumWindows(_enum, None)
            return closed
        except Exception:
            return False

    @staticmethod
    def close_process(process_name: str) -> int:
        """
        Zakończ proces w normalny sposób:
        1. najpierw WM_CLOSE do okien (graceful),
        2. potem proc.terminate() (SIGTERM-like),
        3. na końcu kill() jako fallback.
        Zwraca liczbę zakończonych procesów.
        """
        try:
            import psutil
        except ImportError:
            return 0

        closed = 0
        targets: list = []
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if (proc.info['name']
                        and proc.info['name'].lower() == process_name.lower()):
                    targets.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if not targets:
            return 0

        # 1. Graceful – WM_CLOSE
        for proc in targets:
            try:
                SystemController._close_windows_for_pid(proc.pid)
            except Exception:
                pass

        # 2. Daj chwilę na zamknięcie i sprawdź czy zakończony
        gone, alive = psutil.wait_procs(targets, timeout=1.5)
        closed += len(gone)

        # 3. Pozostałym wyślij terminate (normal)
        for proc in alive:
            try:
                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if alive:
            gone2, still_alive = psutil.wait_procs(alive, timeout=1.0)
            closed += len(gone2)
            # 4. Fallback: kill
            for proc in still_alive:
                try:
                    proc.kill()
                    closed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        if closed:
            logger.info(f"Zamknięto {closed} proces(ów) '{process_name}'")
        return closed

    @staticmethod
    def get_running_processes() -> list[str]:
        """Pobierz listę nazw uruchomionych procesów (unikalne)."""
        try:
            import psutil
            names = set()
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name']:
                        names.add(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return sorted(names)
        except Exception as e:
            logger.error(f"Nie udało się pobrać listy procesów: {e}")
            return []

    @staticmethod
    def get_apps_with_windows() -> list[dict]:
        """Pobierz listę aplikacji z widocznymi oknami (do pickera blokad)."""
        try:
            import psutil
            import win32gui
            import win32process

            pids_to_title: dict[int, str] = {}

            def _callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            if pid not in pids_to_title:
                                pids_to_title[pid] = title
                        except Exception:
                            pass

            win32gui.EnumWindows(_callback, None)

            apps = []
            seen: set[str] = set()
            for pid, title in pids_to_title.items():
                try:
                    proc = psutil.Process(pid)
                    name = proc.name()
                    key = name.lower()
                    if key not in seen:
                        seen.add(key)
                        try:
                            exe_path = proc.exe()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            exe_path = name
                        apps.append({
                            "process_name": name,
                            "display_name": title,
                            "exe_path": exe_path,
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            return sorted(apps, key=lambda x: x["display_name"].lower())
        except Exception as e:
            logger.error(f"Nie udało się pobrać listy aplikacji: {e}")
            return []

    # ─── Aktywne okno ───────────────────────────────────────────

    @staticmethod
    def get_active_window_info() -> Tuple[str, str]:
        """
        Pobierz informacje o aktywnym oknie.
        Zwraca: (tytuł_okna, nazwa_procesu)
        """
        try:
            import win32gui
            import win32process
            import psutil

            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "Nieznany"

            return window_title, process_name
        except Exception as e:
            logger.error(f"Nie udało się pobrać info o aktywnym oknie: {e}")
            return "", "Nieznany"
