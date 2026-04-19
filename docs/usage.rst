Obsługa aplikacji
==================

Po uruchomieniu ``python main.py`` pojawia się okno główne z trzema
zakładkami: **PROFILES**, **SCHEDULE**, **SYSTEM**. W zasobniku systemowym
(tray) widoczna jest ikonka z menu kontekstowym pozwalającym szybko
aktywować profile bez otwierania okna.

Zakładka 01 // PROFILES
-----------------------

Lista kart profili. Na każdej karcie:

* **SWITCH** – aktywuj profil (jeśli profil ma hasło, pojawi się monit,
  patrz :func:`gui.password_utils.request_profile_password`).
  Ponowne kliknięcie na aktywnym profilu go dezaktywuje.
* **EDIT** – otwiera :class:`gui.profile_editor.ProfileEditorDialog`
  do edycji akcji i blokowanych stron.
* **DELETE** – usuwa profil (po potwierdzeniu).

Na dole listy znajduje się przycisk **NEW PROFILE** tworzący nowy,
pusty profil.

Karty profili serwerowych są oznaczone – nie można ich edytować
ani usuwać (tylko aktywować).

Zakładka 02 // SCHEDULE
-----------------------

Tygodniowy kalendarz z blokami. Dodawanie / usuwanie bloków:
:class:`gui.schedule_widget.WeeklyCalendarWidget`.

* Lokalne bloki można kolidować z własnymi – ale **nie** z blokami
  serwerowymi. Próba dodania kolidującego bloku zostanie odrzucona
  (:meth:`core.scheduler.Scheduler.add_block`).
* Bloki serwerowe są oznaczone i nie można ich usunąć lokalnie.
* Gdy czas wchodzi w blok, aplikacja sama aktywuje profil
  (:meth:`core.scheduler.Scheduler._check`).

Ręczne przerwanie bloku
~~~~~~~~~~~~~~~~~~~~~~~

Jeśli użytkownik *lokalnie* przełączy profil w trakcie bloku lub
dezaktywuje go, blok **nie zostanie ponownie uruchomiony** aż do
następnego przedziału czasowego (zapamiętany w ``_skipped_block_keys``).

Wyjątek: bloki z ``source = "server"`` – tych nie można pominąć. Przy
próbie pojawi się okno ``LOCKED // SERVER SCHEDULE``.

Zakładka 03 // SYSTEM
---------------------

Informacje o aplikacji i krótki przewodnik. W nagłówku okna widoczne są:

* ``CLOUD // ...`` – status synchronizacji MongoDB.
* ``SYNC`` – przycisk ręcznej synchronizacji.
* ``STATUS // IDLE`` / ``ACTIVE // <NAZWA>`` – aktywny profil.

Tryby uruchomienia
------------------

.. code-block:: bash

   python main.py              # offline (domyślny)
   python main.py online       # online – sync z MongoDB

W trybie offline ignorowane są wszystkie profile i bloki ze źródłem
``"server"`` (wyfiltrowane w ``MainWindow.__init__``). Pliki na dysku
pozostają – przy kolejnym uruchomieniu *online* ``MongoSync`` odtworzy je.

Co się dzieje przy aktywacji profilu?
-------------------------------------

:meth:`core.profile_manager.ProfileManager.switch_profile`:

1. Dezaktywuje poprzedni profil (jeśli był aktywny).
2. Zapamiętuje aktualny stan systemu (tapeta, motyw) do
   ``_previous_state``.
3. Dla każdej akcji z profilu woła ``Action.execute()``:

   * ``set_theme`` – pisze do rejestru
     ``HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize``
     (klucze ``AppsUseLightTheme``, ``SystemUsesLightTheme``).
   * ``set_wallpaper`` – woła ``SystemParametersInfoW``
     (``SPI_SETDESKWALLPAPER``).
   * ``launch_app`` – rozwiązuje ścieżkę przez ``PATH`` i rejestr
     ``App Paths``, potem ``subprocess.Popen``.
   * ``block_process`` – zamyka proces, a ``ProfileManager`` zapamiętuje
     go do dalszego egzekwowania.

4. Emituje sygnał ``profileChanged`` – GUI przerysowuje karty
   i ikonkę w tray.
5. Zapisuje nowy stan do ``data/active.json``.

Egzekwowanie blokad
~~~~~~~~~~~~~~~~~~~

W MainWindow uruchamiany jest timer co 5 s, który woła
:meth:`core.profile_manager.ProfileManager.enforce_blocks` – jeśli
zablokowany proces został ponownie uruchomiony, zostanie ponownie
zamknięty przez :meth:`core.system_controller.SystemController.close_process`.

Procedura zamykania jest **graceful → twarda**:

1. ``WM_CLOSE`` do wszystkich widocznych okien procesu (``win32gui``).
2. Czeka 1.5 s – jeśli proces sam zniknął, koniec.
3. ``psutil.Process.terminate()``.
4. Fallback: ``kill()``.

Dezaktywacja profilu
~~~~~~~~~~~~~~~~~~~~

:meth:`core.profile_manager.ProfileManager.deactivate_profile` przywraca
zapamiętany stan (tapeta, motyw) i przestaje egzekwować blokady. Akcje
typu ``launch_app`` **nie są cofane** (aplikacje zostają uruchomione),
akcje ``block_process`` nie cofają nic (blokada to „od teraz”).

Integracja z rozszerzeniem Chrome
---------------------------------

Przy starcie ``main.py`` uruchamia w osobnym wątku serwer Flask
(:mod:`extension.server`) na porcie ``8765``. Rozszerzenie odpytuje go
o aktywny profil i listę blokowanych witryn. Szczegóły: :doc:`extension`.

.. note::
   Serwer to wątek *daemon* – kończy się razem z aplikacją. Jeżeli
   chcesz uruchomić serwer niezależnie (np. do testów),
   wywołaj ``python extension/server.py``.
