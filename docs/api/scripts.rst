Skrypty pomocnicze
====================

``scripts.seed_mongo``
----------------------

Wypełnia bazę MongoDB przykładowymi danymi (użytkownicy, profile,
harmonogramy). Wywoływany przez :file:`setup.py` podczas automatycznego
setupu, można też uruchomić ręcznie.

.. code-block:: bash

   python scripts/seed_mongo.py
   python scripts/seed_mongo.py --drop
   python scripts/seed_mongo.py --uri mongodb://localhost:27017 --db timeguard

.. automodule:: seed_mongo
   :members:
   :undoc-members:
   :show-inheritance:

``setup.py``
------------

Skrypt przygotowujący środowisko (zależności, MongoDB, config, seed,
instrukcja rozszerzenia). Opis użycia: :doc:`../installation`.

.. automodule:: setup
   :members:
   :undoc-members:
   :show-inheritance:
