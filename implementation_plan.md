# Context Switcher Pro – Plan Implementacji

Samo-enforsujący się planer dnia, który pozwala jednym kliknięciem przełączyć całe środowisko Windows między profilami (Praca, Nauka, Rozrywka). Profile kontrolują aplikacje, głośność, tapetę, motyw, plan zasilania i blokowanie rozpraszaczy. Wbudowany monitor przebodźcowania śledzi aktywność i ostrzega użytkownika.

## Stos Technologiczny

| Warstwa | Wybór | Powód |
|---|---|---|
| Język | **Python 3.11+** | Szybki rozwój, bogate API Windows |
| GUI | **PySide6** (Qt6) | Licencja LGPL, stylowanie QSS, sygnały/sloty |
| Głośność | **pycaw + comtypes** | Windows Core Audio API |
| Tapeta | **ctypes** (`SystemParametersInfoW`) | Natywne, natychmiastowe |
| Motyw ciemny/jasny | **winreg** | Klucze rejestru `Personalize` |
| Plan zasilania | **subprocess → powercfg** | Standardowe CLI Windows |
| Aktywne okno | **pywin32** + **psutil** | Tytuł okna + nazwa procesu |
| Zarządzanie procesami | **psutil** + **subprocess** | Zabijanie/uruchamianie procesów |
| Analiza AI | **Silnik regułowy** (wbudowany) | Punktacja słów kluczowych dla przebodźcowania |
| Przechowywanie danych | **Pliki JSON** | `profiles.json`, `overrides.json`, `schedule.json` |

## Struktura Projektu

```
Hacknarok/
├── main.py                    # Punkt wejścia
├── requirements.txt           # Zależności
├── data/                      # Magazyn JSON (tworzony w runtime)
├── assets/icons/              # Ikony
├── core/                      # Logika biznesowa
│   ├── profile_manager.py     # ProfileManager, Profile
│   ├── actions.py             # Klasy akcji
│   ├── system_controller.py   # Wrappery Windows API
│   ├── scheduler.py           # Harmonogram przełączania
│   └── overload_monitor.py    # Monitor przebodźcowania
├── gui/                       # Interfejs PySide6
│   ├── main_window.py         # Główne okno
│   ├── profile_card.py        # Karta profilu
│   ├── profile_editor.py      # Edytor profilu
│   ├── schedule_widget.py     # Widget harmonogramu
│   ├── overload_widget.py     # Wskaźnik przebodźcowania
│   └── styles.py              # Style QSS
└── README.md
```

## Komponenty

### 1. System Controller – Wrappery Windows API
- `launch_app()`, `kill_process()`, `set_volume()`, `set_wallpaper()`
- `set_theme()`, `set_power_plan()`, `get_active_window_info()`

### 2. Actions – Klasy akcji profilu
- `LaunchAppAction`, `KillProcessAction`, `SetVolumeAction`
- `SetWallpaperAction`, `SetThemeAction`, `SetPowerPlanAction`, `BlockProcessAction`
- Każda z `execute()` i `undo()` + serializacja JSON

### 3. Profile Manager – Zarządzanie profilami
- CRUD profili, zapis/odczyt JSON
- `switch_profile()` – snapshot stanu → wykonanie akcji → sygnał

### 4. Scheduler – Harmonogram
- `QTimer` co 30s, porównanie z `schedule.json`
- Automatyczne przełączanie profili wg dnia/godziny

### 5. Monitor Przebodźcowania
- Polling co 2s aktywnego okna
- Silnik regułowy: słowniki słów kluczowych z wagami
- Skala 0–10, kolorowy pasek (zielony→żółty→pomarańczowy→czerwony)

### 6. GUI – Ciemny motyw premium
- Glassmorphism, gradienty, animacje hover
- Karty profili z przyciskiem przełączania
- Edytor profilu (dialog)
- Widget harmonogramu
- Wskaźnik przebodźcowania z historią

## Status: ✅ ZATWIERDZONY – implementacja w toku
