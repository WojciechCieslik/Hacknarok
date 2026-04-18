"""
SystemController – wrapper na Windows API.

Hermetyzuje wszystkie wywołania systemowe:
głośność, tapeta, motyw, plan zasilania, procesy, aktywne okno.
"""

import ctypes
import os
import subprocess
import winreg
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SystemController:
    """Kontroler systemowy – enkapsuluje wywołania Windows API."""

    # ─── Głośność ───────────────────────────────────────────────

    @staticmethod
    def _audio_endpoint_volume():
        """Zwróć interfejs IAudioEndpointVolume (obsługuje różne wersje pycaw)."""
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        speakers = AudioUtilities.GetSpeakers()
        # Stara pycaw zwraca IMMDevice (COM) → ma .Activate()
        # Nowa pycaw opakowuje je w AudioDevice → trzeba użyć ._dev
        device = speakers
        if not hasattr(device, "Activate"):
            device = getattr(device, "_dev", device)
        interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))

    @staticmethod
    def get_volume() -> int:
        """Pobierz aktualny poziom głośności (0-100)."""
        try:
            vol = SystemController._audio_endpoint_volume()
            return int(round(vol.GetMasterVolumeLevelScalar() * 100))
        except Exception as e:
            logger.error(f"Nie udało się pobrać głośności: {e}")
            return 50

    @staticmethod
    def set_volume(level: int) -> bool:
        """Ustaw głośność systemową (0-100)."""
        try:
            level = max(0, min(100, level))
            vol = SystemController._audio_endpoint_volume()
            vol.SetMasterVolumeLevelScalar(level / 100.0, None)
            logger.info(f"Głośność ustawiona na {level}%")
            return True
        except Exception as e:
            logger.error(f"Nie udało się ustawić głośności: {e}")
            return False

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

    # ─── Plan zasilania ─────────────────────────────────────────

    @staticmethod
    def _run_cmd(args: list[str]) -> str:
        """Uruchom polecenie i zwróć stdout jako str (obsługa polskiego OEM cp1250)."""
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if not result.stdout:
            return ""
        for enc in ("cp1250", "utf-8", "cp852", "ascii"):
            try:
                return result.stdout.decode(enc)
            except UnicodeDecodeError:
                continue
        return result.stdout.decode("ascii", errors="replace")

    @staticmethod
    def get_power_plans() -> list[dict]:
        """Pobierz listę dostępnych planów zasilania."""
        try:
            output = SystemController._run_cmd(["powercfg", "/list"])
            plans = []
            for line in output.splitlines():
                if "GUID" in line:
                    # Format: "GUID planu zasilania: <guid>  (nazwa) *"
                    parts = line.split(":")
                    if len(parts) >= 2:
                        rest = parts[1].strip()
                        guid = rest.split()[0] if rest.split() else ""
                        # Wyciągnij nazwę z nawiasów
                        name_start = line.find("(")
                        name_end = line.find(")")
                        name = line[name_start + 1:name_end] if name_start != -1 and name_end != -1 else guid
                        is_active = "*" in line
                        plans.append({
                            "guid": guid,
                            "name": name,
                            "active": is_active
                        })
            return plans
        except Exception as e:
            logger.error(f"Nie udało się pobrać planów zasilania: {e}")
            return []

    @staticmethod
    def get_active_power_plan() -> Optional[str]:
        """Pobierz GUID aktywnego planu zasilania."""
        plans = SystemController.get_power_plans()
        for plan in plans:
            if plan["active"]:
                return plan["guid"]
        return None

    @staticmethod
    def set_power_plan(guid: str) -> bool:
        """Ustaw plan zasilania wg GUID."""
        try:
            result = subprocess.run(
                ["powercfg", "/setactive", guid],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                logger.info(f"Plan zasilania zmieniony na: {guid}")
                return True
            else:
                logger.error(f"Błąd powercfg: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Nie udało się zmienić planu zasilania: {e}")
            return False

    # ─── Procesy / Aplikacje ────────────────────────────────────

    @staticmethod
    def launch_app(path: str, args: list[str] = None) -> bool:
        """Uruchom aplikację."""
        try:
            cmd = [path] + (args or [])
            subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
            logger.info(f"Uruchomiono: {path}")
            return True
        except Exception as e:
            logger.error(f"Nie udało się uruchomić {path}: {e}")
            return False

    @staticmethod
    def kill_process(process_name: str) -> bool:
        """Zabij wszystkie procesy o danej nazwie."""
        try:
            import psutil
            killed = 0
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                        proc.terminate()
                        killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            logger.info(f"Zakończono {killed} proces(ów) '{process_name}'")
            return killed > 0
        except Exception as e:
            logger.error(f"Nie udało się zakończyć procesu {process_name}: {e}")
            return False

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
                        apps.append({"process_name": name, "display_name": title})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            return sorted(apps, key=lambda x: x["display_name"].lower())
        except Exception as e:
            logger.error(f"Nie udało się pobrać listy aplikacji: {e}")
            return []

    @staticmethod
    def suspend_process(process_name: str) -> bool:
        """Zawieś (zamroź) wszystkie procesy o danej nazwie."""
        try:
            import psutil
            suspended = 0
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                        proc.suspend()
                        suspended += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            logger.info(f"Zawieszono {suspended} proces(ów) '{process_name}'")
            return suspended > 0
        except Exception as e:
            logger.error(f"Nie udało się zawiesić procesu {process_name}: {e}")
            return False

    @staticmethod
    def resume_process(process_name: str) -> bool:
        """Wznów zawieszone procesy o danej nazwie."""
        try:
            import psutil
            resumed = 0
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                        proc.resume()
                        resumed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            logger.info(f"Wznowiono {resumed} proces(ów) '{process_name}'")
            return resumed > 0
        except Exception as e:
            logger.error(f"Nie udało się wznowić procesu {process_name}: {e}")
            return False

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
