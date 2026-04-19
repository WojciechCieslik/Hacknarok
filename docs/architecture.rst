Architektura
============

Time Guard dzieli się na pięć warstw:

1. **Dane** – pliki JSON w :file:`data/` (źródło prawdy *lokalnie*).
2. **Synchronizacja z chmurą** – :mod:`core.mongo_sync` (opcjonalna).
3. **Logika domenowa** – :mod:`core.profile_manager`,
   :mod:`core.scheduler`, :mod:`core.actions`.
4. **Integracja z systemem operacyjnym** – :mod:`core.system_controller`.
5. **Prezentacja** – GUI (:mod:`gui`) oraz serwer HTTP rozszerzenia
   (:mod:`extension.server`).

Warstwa danych
--------------

============================  ============================================
Plik                           Odpowiedzialność
============================  ============================================
``data/config.json``           Adres + creds do MongoDB, user_id, interval
``data/active.json``           Nazwa aktualnie aktywnego profilu
``data/profiles/<name>.json``  Jeden plik = jeden profil
``data/schedule.json``         Lista bloków harmonogramu (tygodniowych)
``data/profiles.json``         Legacy – migrowany przy starcie
============================  ============================================

Wszyscy czytają te pliki *niezależnie* – scheduler, GUI, serwer
rozszerzenia. Dzięki temu edycja w GUI jest natychmiast widoczna
w rozszerzeniu bez dodatkowej magistrali komunikacyjnej.

MongoDB jako źródło prawdy (tryb online)
----------------------------------------

:class:`core.mongo_sync.MongoSync` robi **read-only pull** co
``sync_interval_sec``:

1. Pobiera ``user_schedules.find_one({"user_id": ...})``.
2. Pobiera ``profiles.find({"user_id": ...})``.
3. Zapisuje profile do ``data/profiles/`` z flagą ``source="server"``.
4. Merge'uje harmonogram: lokalne bloki zostają, serwerowe są
   zastępowane; bloki lokalne kolidujące z serwerowymi są odrzucane.

Po zapisie emituje sygnał ``dataUpdated`` – GUI przeładowuje stan.

Logika domenowa
---------------

``ProfileManager`` (:mod:`core.profile_manager`)
   Trzyma listę profili, aktywny profil oraz ``_previous_state``
   (tapeta/motyw sprzed aktywacji, żeby go przywrócić). Udostępnia
   sygnały Qt: ``profileChanged``, ``profilesUpdated``.

``Scheduler`` (:mod:`core.scheduler`)
   Qt-owy ``QTimer`` co 20 s sprawdza, czy bieżący czas wchodzi / wychodzi
   z bloku. Emituje ``scheduleTriggered`` (start bloku) i ``scheduleEnded``
   (koniec). Zapamiętuje ręcznie pominięte bloki lokalne.

``Action`` + rejestr (:mod:`core.actions`)
   Klasa bazowa z metodami ``execute()`` / ``undo()`` / ``to_dict()`` /
   ``from_dict()``. Słownik ``ACTION_REGISTRY`` mapuje string ``type``
   z JSON na konkretną klasę. Dodanie nowego typu akcji =
   1) napisać klasę dziedziczącą po ``Action``,
   2) dopisać do ``ACTION_REGISTRY``.

Warstwa systemowa
-----------------

:class:`core.system_controller.SystemController` hermetyzuje **wszystkie**
wywołania WinAPI:

* ``ctypes.windll.user32.SystemParametersInfoW`` – tapeta.
* ``winreg`` + ``HKCU\...\Personalize`` – motyw.
* ``psutil`` – listowanie procesów, ``terminate()`` / ``kill()``.
* ``win32gui`` / ``win32process`` – okna, aktywne okno, WM_CLOSE.
* ``subprocess.Popen`` + rejestr ``App Paths`` – uruchamianie aplikacji.

Wszystkie metody są ``@staticmethod``, bo nie trzymają stanu.

Warstwa prezentacji
-------------------

GUI (:mod:`gui`) – PySide6
   Pojedyncze okno :class:`gui.main_window.MainWindow` z trzema
   zakładkami. Komponenty:

   * :class:`gui.profile_card.ProfileCard` – karta profilu na liście
   * :class:`gui.profile_editor.ProfileEditorDialog` – edycja akcji
   * :class:`gui.schedule_widget.WeeklyCalendarWidget` – kalendarz tygodniowy
   * :mod:`gui.styles` – motyw (QSS + paleta kolorów)

Serwer HTTP (:mod:`extension.server`) – Flask
   Uruchamiany jako *daemon thread* z :func:`main._start_extension_server`
   albo standalone (``python extension/server.py``). Czyta / modyfikuje
   te same pliki w ``data/`` co GUI – ``FILE_LOCK`` zapewnia spójność.

Cykl życia uruchomienia
-----------------------

.. code-block:: text

   main()
     ├── _parse_mode(argv)                   # online / offline
     ├── QApplication(sys.argv)
     ├── threading.Thread(_start_extension_server, daemon=True)
     │     └── Flask.app.run(port=8765)
     └── MainWindow(online=...)
           ├── ProfileManager()              # ładuje data/profiles/
           ├── Scheduler()                   # ładuje data/schedule.json
           ├── [online] MongoSync(self)
           ├── _setup_ui()
           ├── _setup_tray()
           ├── scheduler.start()             # QTimer 20 s
           ├── _block_timer.start()          # QTimer 5 s – enforce_blocks
           └── [online] mongo_sync.start_auto_sync()

Sygnały Qt – mapa przepływu
---------------------------

.. code-block:: text

   Scheduler.scheduleTriggered(str)  ──► MainWindow._on_schedule_trigger
       ProfileManager.switch_profile(manual=False)

   Scheduler.scheduleEnded(str)      ──► MainWindow._on_schedule_end
       ProfileManager.deactivate_profile()

   ProfileCard.switchClicked(str)    ──► MainWindow._on_card_switch
       ProfileManager.switch_profile(manual=True)

   ProfileManager.profileChanged     ──► MainWindow._on_profile_changed
       (odśwież UI, tray, badge)

   MongoSync.dataUpdated             ──► MainWindow._on_cloud_data_updated
       (przeładuj ProfileManager + Scheduler)

Model bezpieczeństwa
--------------------

* **Profile blokowane hasłem** (``locked = true``) – SHA-256 hasła.
  Wymagane do: aktywacji, edycji, usunięcia oraz operacji na liście
  blokowanych stron z rozszerzenia. Patrz
  :func:`gui.password_utils.request_profile_password` oraz
  :func:`extension.server.verify_password`.

* **Profile serwerowe** – nie można ich edytować ani usunąć lokalnie
  (:meth:`core.profile_manager.ProfileManager.update_profile` i
  :meth:`core.profile_manager.ProfileManager.delete_profile` zwracają
  ``False``). Serwer wymusza.

* **Bloki serwerowe** – nie można ich pominąć; mają priorytet nad
  kolidującymi blokami lokalnymi (te są odrzucane).
