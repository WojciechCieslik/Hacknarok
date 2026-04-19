"""
Konfiguracja Sphinx dla dokumentacji Time Guard.

Dokumentacja pod adresem: https://www.sphinx-doc.org/
"""

import os
import sys

# -- Ścieżki projektu --------------------------------------------------------

# Dodaj korzeń projektu do sys.path, żeby autodoc zobaczył pakiety core/, gui/.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "extension"))
sys.path.insert(0, os.path.join(_ROOT, "scripts"))


# -- Informacje o projekcie --------------------------------------------------

project = "Time Guard"
author = "Time Guard Team"
copyright = "2026, Time Guard Team"
release = "1.0"
version = "1.0"


# -- Konfiguracja Sphinx -----------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

language = "pl"


# -- Opcje HTML --------------------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = f"Time Guard {release} – dokumentacja"
html_short_title = "Time Guard"

# Fallback, jeśli motyw RTD nie jest zainstalowany.
try:
    import sphinx_rtd_theme  # noqa: F401
except ImportError:
    html_theme = "alabaster"


# -- Autodoc -----------------------------------------------------------------

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}

# Moduły systemowe Windows + zewnętrzne zależności, których nie da się
# zaimportować na maszynie budującej dokumentację (np. Linux / CI).
# Bez tej listy autodoc wyrzuciłby ImportError przy importowaniu modułów
# używających winreg, ctypes.windll, pywin32 itp.
autodoc_mock_imports = [
    "winreg",
    "win32gui",
    "win32process",
    "win32con",
    "pywin32",
    "pycaw",
    "comtypes",
    "psutil",
    "pymongo",
    "flask",
    "flask_cors",
    "PySide6",
    "shiboken6",
]

autoclass_content = "both"         # docstring klasy + __init__
autodoc_typehints = "description"  # type hinty w opisie, nie w sygnaturze


# -- Napoleon (Google / NumPy style docstrings) ------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False


# -- Intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pymongo": ("https://pymongo.readthedocs.io/en/stable/", None),
    "flask": ("https://flask.palletsprojects.com/en/latest/", None),
}


# -- Todo --------------------------------------------------------------------

todo_include_todos = True
