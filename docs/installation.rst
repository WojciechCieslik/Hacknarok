Instalacja i uruchomienie
==========================

Wymagania wstępne
-----------------

Przed uruchomieniem upewnij się, że masz:

* Python 3.11 lub nowszy (``python --version``)
* ``pip``
* **Jedno z poniższych** do uruchomienia MongoDB:

  * Docker Desktop (zalecane – projekt zawiera ``docker-compose.yml``)
  * lub lokalną instalację *MongoDB Community Server* (``mongod``)

.. tip::
   Dla trybu ``offline`` MongoDB nie jest potrzebne – aplikacja działa
   wtedy wyłącznie na plikach w katalogu ``data/``.

Automatyczny setup (``setup.py``)
---------------------------------

Projekt zawiera skrypt ``setup.py``, który **jednym poleceniem** przygotowuje
całe środowisko. Uruchom go z katalogu głównego projektu:

.. code-block:: bash

   python setup.py

Skrypt wykonuje 5 kroków:

1. **Sprawdza / instaluje zależności Python** – ``pymongo``, ``flask``,
   ``flask_cors``, ``PySide6``, ``psutil``. Jeśli czegoś brakuje, instaluje
   z ``requirements.txt``.

2. **Uruchamia lokalną bazę MongoDB** – w następującej kolejności:

   a. Sprawdza czy ``mongod`` już nasłuchuje na ``localhost:27017``.
   b. Próbuje ``docker compose up -d`` (lub starsze ``docker-compose``).
   c. Próbuje uruchomić systemowe ``mongod``.
   d. Jeśli żadne nie zadziała – kończy z komunikatem błędu i linkami
      do pobrania Docker Desktop / MongoDB Community.

3. **Tworzy ``data/config.json``** wskazujący na ``mongodb://localhost:27017``.
   Jeżeli istnieje już plik wskazujący na Atlas (chmurowy), pokaże
   ostrzeżenie i nadpisze (można wrócić do Atlas ręcznie – patrz
   :doc:`configuration`).

4. **Seeduje bazę** przez :mod:`scripts.seed_mongo` – wstawia przykładowych
   użytkowników, profile i harmonogramy.

5. **Wypisuje instrukcję instalacji rozszerzenia Chrome** (instalacji
   rozszerzenia nie da się w pełni zautomatyzować – Chrome tego nie
   pozwala). Patrz :doc:`extension`.

Po zakończeniu:

.. code-block:: bash

   python main.py                 # tryb offline (domyślny)
   python main.py online          # tryb online + sync z MongoDB

Ręczna instalacja (krok po kroku)
---------------------------------

Jeśli wolisz mieć kontrolę nad każdym krokiem (np. na Linuksie dla
potrzeb developerskich albo wdrażasz na Atlas):

1. **Zależności Python**:

   .. code-block:: bash

      pip install -r requirements.txt

   ``requirements.txt`` zawiera m.in. ``PySide6``, ``Flask``, ``pymongo``,
   ``psutil``, ``pywin32``, ``pycaw``.

2. **MongoDB przez Docker**:

   .. code-block:: bash

      docker compose up -d

   Plik :file:`docker-compose.yml` w katalogu głównym podnosi
   ``mongo:7`` na porcie ``27017`` z wolumenem ``timeguard_data``.

3. **Konfiguracja**:

   .. code-block:: bash

      cp data/config.example.json data/config.json
      # edytuj data/config.json – ustaw mongodb_uri i user_id

   Szczegóły wszystkich pól: :doc:`configuration`.

4. **Seed bazy** (opcjonalnie):

   .. code-block:: bash

      python scripts/seed_mongo.py
      python scripts/seed_mongo.py --drop  # wyczyść kolekcje przed seedem

5. **Uruchom aplikację**:

   .. code-block:: bash

      python main.py

Argumenty wiersza poleceń
-------------------------

Plik :file:`main.py` akceptuje opcjonalny argument pozycyjny:

=================  ===========================================================
Argument            Efekt
=================  ===========================================================
*(brak)*            Tryb **offline**, nie łączy się z MongoDB
``offline``         To samo, jawnie
``--offline``       To samo, styl "flagi"
``online``          Tryb **online**, synchronizacja z MongoDB przy starcie
``--online``        To samo, styl "flagi"
=================  ===========================================================

Patrz :func:`main._parse_mode`.

Zależności zewnętrzne
---------------------

Pełna lista wersji znajduje się w :file:`requirements.txt`. Najważniejsze:

======================  ============================================
Pakiet                   Do czego służy
======================  ============================================
``PySide6``              GUI (Qt 6)
``Flask``, ``flask-cors`` Serwer lokalny na porcie 8765 dla rozszerzenia
``pymongo``              Klient MongoDB dla :mod:`core.mongo_sync`
``psutil``               Listowanie i kończenie procesów
``pywin32``              WinAPI (``win32gui``, ``win32process``, ``win32con``)
``pycaw``                (rezerwowe) sterowanie audio
======================  ============================================

Budowanie tej dokumentacji
--------------------------

Zainstaluj Sphinx z motywem Read the Docs:

.. code-block:: bash

   pip install sphinx sphinx-rtd-theme

Następnie:

.. code-block:: bash

   cd docs
   make html            # Linux / macOS
   make.bat html        # Windows

Wygenerowany HTML znajdziesz w :file:`docs/_build/html/index.html`.

.. note::
   Dokumentacja importuje moduły projektu przez ``sphinx.ext.autodoc``.
   Na systemach innych niż Windows moduły takie jak ``winreg`` czy
   ``pywin32`` nie istnieją – dlatego ``conf.py`` używa
   ``autodoc_mock_imports``, który tworzy dla nich atrapy. Dzięki temu
   dokumentację można budować także na CI / Linuksie.
