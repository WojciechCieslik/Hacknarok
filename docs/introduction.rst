Wprowadzenie
============

Po co to komu?
--------------

Typowy dzień wymaga przełączania się między bardzo różnymi kontekstami:
*praca*, *nauka*, *rozrywka*. Każdy z nich ma inne wymagania co do środowiska:

* **Praca** – ciemny motyw, Spotify i Discord zamknięte, YouTube zablokowany.
* **Nauka** – jasny motyw, zamknięte rozpraszacze, tapeta skupiająca.
* **Rozrywka** – wszystko dozwolone, ciemny motyw.

Ręczne przestawianie tych rzeczy jest męczące i łatwo o nich zapomnieć.
Time Guard automatyzuje cały proces: **jedno kliknięcie = całe środowisko
skonfigurowane pod dany kontekst.**

Kluczowe funkcje
----------------

Profile środowiska
   Każdy profil ma: ikonę, kolor, opis, listę *akcji* do wykonania oraz
   listę *blokowanych stron*. Akcje to klasy implementujące interfejs
   :class:`core.actions.Action` (motyw, tapeta, uruchom apkę, zablokuj
   proces).

Harmonogram tygodniowy
   Każdy blok to trójka *(dzień, od–do, profil)*. Gdy bieżący czas wchodzi
   w blok, aktywowany jest przypisany profil; przy wyjściu z bloku stan
   systemu jest przywracany. Użytkownik może ręcznie przerwać blok –
   nie zostanie on ponownie uruchomiony w tym samym przedziale.

Blokowanie stron (rozszerzenie Chrome)
   Rozszerzenie (Manifest V3) komunikuje się z lokalnym serwerem Flask
   (:mod:`extension.server`) na porcie ``8765``, pobiera z niego aktywny
   profil oraz listę blokowanych witryn i blokuje je przez
   ``declarativeNetRequest`` + content script (SPA).

Egzekwowanie blokad procesów
   Gdy aktywny profil blokuje aplikację (np. ``discord.exe``) i użytkownik
   ją ponownie uruchomi, :class:`core.profile_manager.ProfileManager`
   co kilka sekund ją zamyka (graceful ``WM_CLOSE`` → ``terminate`` → ``kill``).

Tryb online / offline
   Aplikacja uruchamia się w dwóch trybach (argument wiersza poleceń):

   * ``offline`` (domyślny) – używa tylko lokalnych plików w ``data/``.
   * ``online`` – dodatkowo synchronizuje profile i harmonogram
     z MongoDB przy starcie oraz co ``sync_interval_sec`` sekund.

Profile serwerowe
   W trybie online profile z bazy trafiają na dysk z flagą
   ``"source": "server"``. Takich profili nie można edytować ani usuwać
   lokalnie; bloki harmonogramu *serwerowe* mają priorytet nad lokalnymi
   i nie można ich pominąć (funkcja rodzicielska / korporacyjna).

Architektura w skrócie
----------------------

.. code-block:: text

   ┌────────────────┐    pliki JSON     ┌──────────────────┐
   │  MongoDB Atlas │◄──────────────────│ core/mongo_sync  │
   │  (user data)   │   (read-only)     └──────────────────┘
   └────────────────┘                            │
                                                 ▼
                                    ┌─────────────────────────┐
                                    │  data/profiles/*.json   │
                                    │  data/schedule.json     │
                                    │  data/active.json       │
                                    └─────────────┬───────────┘
                          ┌───────────────────────┼──────────────────────┐
                          ▼                       ▼                      ▼
             ┌────────────────────┐   ┌──────────────────┐   ┌──────────────────────┐
             │ core/profile_mgr   │   │ core/scheduler   │   │ extension/server.py  │
             │ (stan + akcje)     │   │ (bloki czasowe)  │   │ (Flask :8765)        │
             └──────────┬─────────┘   └────────┬─────────┘   └──────────┬───────────┘
                        │                      │                        │
                        ▼                      ▼                        ▼
             ┌────────────────────┐   ┌──────────────────┐   ┌──────────────────────┐
             │ SystemController   │   │  Qt Timer 20s    │   │   Chrome extension   │
             │ (winreg / ctypes)  │   │                  │   │   (MV3)              │
             └────────────────────┘   └──────────────────┘   └──────────────────────┘

Wszystkie trzy konsumentów danych (GUI, scheduler, serwer rozszerzenia)
czytają ten sam format plików w ``data/``, więc zmiana wprowadzona w
jednym miejscu jest natychmiast widoczna w pozostałych.

Wymagania systemowe
-------------------

* **System operacyjny:** Windows 10/11 (obecna implementacja
  :class:`core.system_controller.SystemController` zależy od ``winreg``
  i ``pywin32``).
* **Python:** 3.11+ (testowane na 3.14).
* **MongoDB:** opcjonalnie (Docker lub systemowe ``mongod``).
* **Chrome** lub inna przeglądarka oparta na Chromium (rozszerzenie MV3).
