Rozszerzenie Chrome
====================

Rozszerzenie to *Manifest V3* napisane w JavaScript, które blokuje strony
zgodnie z aktywnym profilem Time Guarda. Komunikuje się z aplikacją przez
lokalny serwer Flask (:mod:`extension.server`) na ``http://localhost:8765``.

.. note::
   Rozszerzenie nie może być zainstalowane automatycznie – Chrome nie
   pozwala na programowe instalowanie rozpakowanych rozszerzeń. Trzeba to
   zrobić **raz** ręcznie (patrz niżej).

Instalacja (jednorazowo)
------------------------

1. Uruchom aplikację przynajmniej raz (``python main.py``) albo wywołaj
   ``python setup.py`` – oba tworzą plik ``data/active.json`` i katalog
   profili.

2. Otwórz Chrome i przejdź do:

   .. code-block:: text

      chrome://extensions

3. Włącz **Tryb dewelopera** (przełącznik w prawym górnym rogu).

4. Kliknij **Załaduj rozpakowane** i wskaż katalog:

   .. code-block:: text

      <katalog projektu>/extension/extension

5. Ikona Time Guard pojawi się w pasku przeglądarki.

.. warning::
   Rozszerzenie działa tylko gdy aplikacja główna (``main.py``) jest
   uruchomiona – wtedy serwer ``:8765`` nasłuchuje i podaje aktualny profil.

Struktura katalogu
------------------

.. code-block:: text

   extension/
   ├── server.py                 # Serwer Flask :8765 (strona Python)
   ├── README.md
   └── extension/                # Folder ładowany w chrome://extensions
       ├── manifest.json         # MV3
       ├── background.js         # Service worker – sync, DNR, alarmy
       ├── content.js            # Wstrzykiwany do stron: SPA navigation
       ├── popup.html/css/js     # UI popupu w pasku
       ├── blocked.html/css/js   # Strona blokady
       └── icon.png

Jak działa blokowanie
---------------------

Rozszerzenie używa **dwóch mechanizmów** w zależności od typu wpisu:

1. **Domeny bez ścieżki** (``facebook.com``, ``youtube.com``)
   → ``declarativeNetRequest`` w ``background.js``. Przeglądarka
   przekierowuje żądanie HTTP do ``blocked.html`` zanim strona się
   załaduje – szybkie i niezawodne.

2. **Wpisy ze ścieżką** (``youtube.com/shorts``)
   → ``content.js`` obserwuje ``history.pushState`` / ``replaceState`` /
   ``popstate``. Przy dopasowaniu robi ``window.location.replace()`` do
   strony blokady.

Podział wynika z ograniczeń MV3: ``declarativeNetRequest`` widzi tylko
żądania HTTP, nie nawigację SPA (np. YouTube nie przeładowuje strony
przy klikaniu w Shorts – robi tylko ``pushState``).

API serwera (:mod:`extension.server`)
-------------------------------------

Źródło prawdy to pliki w :file:`data/profiles/` oraz :file:`data/active.json`
zarządzane przez aplikację Python. Serwer udostępnia:

``GET /state``
   Zwraca aktywny profil + listę dostępnych profili:

   .. code-block:: json

      {
        "activeProfile": "Praca",
        "profile": {
          "name": "Praca",
          "color": "#3b82f6",
          "blockedSites": ["youtube.com", "facebook.com"],
          "locked": false
        },
        "availableProfiles": ["Praca", "Nauka", "Rozrywka"]
      }

``GET /blocked``
   Lista domen blokowanych przez aktywny profil (kompatybilność wsteczna
   ze starszym rozszerzeniem).

``POST /blocked``
   Dodaje stronę do aktywnego profilu. Body: ``{ "site": "...", "password"?: "..." }``.
   Jeśli profil jest zablokowany hasłem, wymagane poprawne ``password``.
   Domena jest normalizowana przez :func:`extension.server.normalize_site`.

``DELETE /blocked``
   Usuwa stronę z aktywnego profilu. Body jak w POST.

Odpowiedzi zawsze w JSON. Wszystkie endpointy są chronione prostym lockiem
(``FILE_LOCK``), żeby nie uszkodzić pliku przy równoczesnych zapisach.

Uprawnienia rozszerzenia (``manifest.json``)
--------------------------------------------

===========================  ==========================================
Uprawnienie                   Do czego
===========================  ==========================================
``declarativeNetRequest``    Blokada domen przez reguły DNR
``tabs``                     Pobieranie URL z aktywnej karty (popup)
``alarms``                   Cykliczna synchronizacja z serwerem
``storage``                  Cache profilu między restartami service workera
``webNavigation``            Obserwacja nawigacji SPA
``host_permissions``          ``http://localhost:8765/*`` + ``<all_urls>``
===========================  ==========================================

Debugowanie
-----------

* Logi service workera: ``chrome://extensions`` → *service worker*
  → *inspect*.
* Logi content scriptu: DevTools na otwartej karcie → zakładka
  **Console**.
* Logi serwera: terminal, w którym uruchomiony jest ``main.py``.
  Poziom ``werkzeug`` jest podniesiony do ``WARNING``, żeby nie spamować.

Problemy i rozwiązania
----------------------

Rozszerzenie pokazuje „Brak profilu / Nie połączono”
   * Sprawdź czy aplikacja główna działa (``python main.py``).
   * Sprawdź ``http://localhost:8765/state`` w przeglądarce – powinno
     zwrócić JSON.
   * Port ``8765`` może być zajęty; można go zmienić w :file:`main.py`
     (``app.run(port=8765, ...)``) oraz w ``extension/background.js``.

Strona nadal się ładuje mimo blokady
   * Jeśli to SPA (np. YouTube Shorts) – wpis musi zawierać ścieżkę
     (``youtube.com/shorts``), żeby content script go złapał.
   * Zrefreshuj rozszerzenie w ``chrome://extensions``.
