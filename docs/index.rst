Time Guard – dokumentacja
==========================

**Time Guard** to samo-egzekwowalny planer dzienny, który jednym kliknięciem
przełącza całe środowisko pracy między trybami (Praca / Nauka / Rozrywka).
Aplikacja zmienia tapetę, motyw systemu, uruchamia/zamyka aplikacje oraz
blokuje wybrane strony w przeglądarce za pomocą własnego rozszerzenia Chrome.

**Slogan:** *Guard Your Focus, Guide Your Day.*

.. note::
   Time Guard działa natywnie pod **Windows** – wykorzystuje Windows API
   (``ctypes``, ``winreg``, ``pywin32``) do zmiany tapety/motywu oraz
   zamykania procesów.

Przegląd
--------

* **Profile środowiska** – każdy profil to zestaw akcji (motyw, tapeta,
  uruchom aplikację, zablokuj proces) i lista blokowanych witryn.
* **Harmonogram tygodniowy** – bloki czasowe automatycznie aktywują
  i dezaktywują profile.
* **Rozszerzenie Chrome** – komunikuje się z aplikacją przez lokalny
  serwer Flask (port ``8765``) i blokuje zdefiniowane witryny.
* **Synchronizacja MongoDB** – w trybie *online* aplikacja pobiera profile
  oraz harmonogram użytkownika z MongoDB (np. Atlas). Serwer jest
  *source-of-truth* — lokalne edycje profili serwerowych są blokowane.
* **Tryb offline** – wszystko działa z plików w katalogu ``data/``.

Spis treści
-----------

.. toctree::
   :maxdepth: 2
   :caption: Przewodnik

   introduction
   installation
   configuration
   usage
   extension
   architecture

.. toctree::
   :maxdepth: 2
   :caption: Referencja API

   api/core
   api/gui
   api/extension
   api/scripts

Indeksy
-------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
