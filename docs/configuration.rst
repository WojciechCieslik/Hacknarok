Konfiguracja
============

Time Guard używa kilku plików JSON w katalogu ``data/``. Wszystkie są
tworzone automatycznie przy pierwszym uruchomieniu (``setup.py`` / start
aplikacji), ale można je edytować ręcznie.

.. contents::
   :local:
   :depth: 2

``data/config.json`` – synchronizacja z MongoDB
-----------------------------------------------

Główny plik konfiguracyjny dla trybu **online**. Szablon leży w
:file:`data/config.example.json`.

.. code-block:: json

   {
     "mongodb_uri": "mongodb://localhost:27017",
     "mongodb_db": "timeguard",
     "user_id": "user_demo",
     "sync_interval_sec": 60
   }

Opis pól
~~~~~~~~

``mongodb_uri`` *(string)*
   Pełny connection string MongoDB. Może wskazywać na lokalną bazę
   (``mongodb://localhost:27017``) albo na Atlas
   (``mongodb+srv://USER:PASS@cluster.xxxxx.mongodb.net/...``).

   Można **nadpisać zmienną środowiskową** ``TIMEGUARD_MONGO_URI`` –
   przydatne gdy nie chcesz trzymać poświadczeń w repozytorium.
   Patrz :func:`core.mongo_sync.load_config`.

``mongodb_db`` *(string)*
   Nazwa bazy. Domyślnie ``"timeguard"``.

``user_id`` *(string)*
   Identyfikator użytkownika. :class:`core.mongo_sync.MongoSync` filtruje
   po nim kolekcje ``profiles`` oraz ``user_schedules``. Skrypt
   :mod:`scripts.seed_mongo` wstawia przykładowo pięciu użytkowników:
   ``user_ania``, ``user_bartek``, ``user_czarek``, ``user_daria``,
   ``user_eryk``.

``sync_interval_sec`` *(int)*
   Co ile sekund robić *pull* z bazy. Minimum 10 (wartości mniejsze są
   zaokrąglane w górę). Domyślnie 60.

Tryb offline
~~~~~~~~~~~~

Plik ``config.json`` **nie jest wymagany** do pracy w trybie offline –
aplikacja po prostu nie próbuje wtedy łączyć się z bazą.

``data/profiles/*.json`` – definicje profili
--------------------------------------------

Każdy profil to pojedynczy plik JSON w :file:`data/profiles/`. Nazwa pliku
pochodzi od nazwy profilu (zamienione są znaki niedozwolone w Windows –
patrz :func:`core.profile_manager._safe_filename`).

Przykład:

.. code-block:: json

   {
     "name": "Praca",
     "icon": "🏢",
     "color": "#3b82f6",
     "description": "Skupienie na pracy – brak rozpraszaczy.",
     "actions": [
       { "type": "set_theme", "dark": true },
       { "type": "block_process", "process_name": "Spotify.exe",
         "display_name": "Spotify" }
     ],
     "blocked_sites": ["youtube.com", "facebook.com"],
     "locked": false,
     "password_hash": "",
     "source": "local"
   }

Pola profilu
~~~~~~~~~~~~

``name``
   Unikalna nazwa. Służy też jako klucz w ``data/active.json``
   i w blokach harmonogramu.

``icon``, ``color``, ``description``
   Wizualne: emoji, kolor akcentu (hex), opis widoczny w GUI.

``actions``
   Lista obiektów z polem ``type``. Obsługiwane typy:

   * ``launch_app`` – ``path``, ``args``, ``label``
     (:class:`core.actions.LaunchAppAction`)
   * ``set_wallpaper`` – ``image_path``
     (:class:`core.actions.SetWallpaperAction`)
   * ``set_theme`` – ``dark`` (bool)
     (:class:`core.actions.SetThemeAction`)
   * ``block_process`` – ``process_name``, ``display_name``
     (:class:`core.actions.BlockProcessAction`)

   Legacy-akcje (``set_power_plan``, ``kill_process``, ``set_volume``)
   są filtrowane przy wczytywaniu w
   :meth:`core.profile_manager.Profile.from_dict`.

``blocked_sites``
   Lista domen (bez ``https://`` / ``www.``) blokowanych przez rozszerzenie.
   Normalizowane przez :func:`extension.server.normalize_site`.

``locked``, ``password_hash``
   Jeśli ``locked = true``, próby aktywacji / edycji / usunięcia profilu
   wymagają hasła. ``password_hash`` to SHA-256 hasła (patrz
   :meth:`core.profile_manager.Profile.verify_password`).

``source``
   ``"local"`` (domyślnie) albo ``"server"``. Profile serwerowe są
   **tylko do odczytu** w GUI – zostaną nadpisane przy następnej
   synchronizacji. Logika w
   :meth:`core.profile_manager.ProfileManager.update_profile`.

``data/active.json`` – aktywny profil
-------------------------------------

.. code-block:: json

   { "active": "Praca" }

Zapisywany / czytany w :meth:`core.profile_manager.ProfileManager._save_active`
oraz :meth:`core.profile_manager.ProfileManager._load_active_name`. Z tego
pliku korzysta też serwer rozszerzenia, żeby wiedzieć który profil
aktualnie egzekwować.

``data/schedule.json`` – harmonogram
------------------------------------

.. code-block:: json

   {
     "blocks": [
       {
         "day": 0,
         "start_hour": 8,  "start_min": 0,
         "end_hour": 12,   "end_min": 0,
         "profile_name": "Praca",
         "enabled": true,
         "source": "local"
       }
     ]
   }

* ``day`` – 0 = Poniedziałek … 6 = Niedziela
* Bloki są **tygodniowe** (powtarzają się co tydzień)
* ``source = "server"`` – blok pochodzi z MongoDB; nie można go usunąć
  ani pominąć (patrz :meth:`core.scheduler.Scheduler.notify_manual_deactivation`)

Obsługiwany jest też legacy-format z polem ``entries`` – jest
automatycznie migrowany do ``blocks`` w :meth:`core.scheduler.Scheduler.load`.

Zmienne środowiskowe
--------------------

=================================  ==========================================
Zmienna                             Znaczenie
=================================  ==========================================
``TIMEGUARD_MONGO_URI``             Nadpisuje ``mongodb_uri`` z ``config.json``
=================================  ==========================================

Struktura kolekcji MongoDB
--------------------------

Dla trybu online aplikacja czyta z trzech kolekcji w bazie wskazanej przez
``mongodb_db``:

``users``
   Metadane użytkowników. Aplikacja sama nie zapisuje do tej kolekcji
   (wypełnia ją tylko :mod:`scripts.seed_mongo`).

``profiles``
   Dokumenty profili, filtrowane po ``user_id``. Pola jak w
   ``data/profiles/*.json`` plus ``user_id`` i ``updated_at``.

``user_schedules``
   Jeden dokument na użytkownika:

   .. code-block:: json

      {
        "user_id": "user_demo",
        "blocks": [ { "day": 0, "start_hour": 8, ... } ],
        "updated_at": "..."
      }

   Pola ``blocks`` są identyczne jak w lokalnym ``schedule.json`` (bez
   pola ``source`` – dodawane jest automatycznie przy zapisie).

.. warning::
   Klient MongoDB w Time Guard jest **read-only**. Zmiany w GUI na
   profilach pochodzących z serwera nie są propagowane do bazy – do tego
   potrzebny byłby osobny panel administracyjny.
