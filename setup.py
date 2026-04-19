"""
setup.py – Jednorazowy setup środowiska dla Time Guard.

Uruchomienie:
    python setup.py

Co robi:
  1. Sprawdza / instaluje zależności Python
  2. Uruchamia lokalną bazę MongoDB (przez Docker lub systemowe mongod)
  3. Tworzy data/config.json wskazujący na localhost
  4. Seeduje bazę przykładowymi danymi
  5. Buduje dokumentację Sphinx (docs/_build/html/)
  6. Wyświetla instrukcję instalacji rozszerzenia Chrome
"""

import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT, "data", "config.json")
EXTENSION_PATH = os.path.join(ROOT, "extension", "extension")
SEED_SCRIPT = os.path.join(ROOT, "scripts", "seed_mongo.py")

MONGO_URI = "mongodb://localhost:27017"
MONGO_DB  = "timeguard"
USER_ID   = "user_demo"
DOCS_DIR  = os.path.join(ROOT, "docs")


# ─── Kolory terminala ────────────────────────────────────────────

def green(s):  return f"\033[92m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"
def red(s):    return f"\033[91m{s}\033[0m"
def bold(s):   return f"\033[1m{s}\033[0m"

def step(n, total, msg):
    print(f"\n{bold(f'[{n}/{total}]')} {msg}")


# ─── Zależności Python ───────────────────────────────────────────

def ensure_dependencies():
    step(1, 6, "Sprawdzam zależności Python...")
    missing = []
    for pkg in ("pymongo", "flask", "flask_cors", "PySide6", "psutil"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(yellow(f"  Brakuje: {', '.join(missing)}. Instaluję..."))
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r",
                                os.path.join(ROOT, "requirements.txt"), "--quiet"])
        # pymongo może nie być w requirements.txt
        try:
            __import__("pymongo")
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pymongo", "--quiet"])
        print(green("  ✓ Zależności zainstalowane"))
    else:
        print(green("  ✓ Wszystkie zależności obecne"))


# ─── MongoDB ─────────────────────────────────────────────────────

def _mongo_is_running() -> bool:
    """Sprawdź czy mongod nasłuchuje na localhost:27017."""
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        client.close()
        return True
    except Exception:
        return False


def _start_via_docker() -> bool:
    """Uruchom MongoDB przez docker compose. Zwraca True jeśli sukces."""
    if not shutil.which("docker"):
        return False
    compose_file = os.path.join(ROOT, "docker-compose.yml")
    if not os.path.exists(compose_file):
        return False
    print("  Uruchamiam kontener Docker z MongoDB...")
    try:
        subprocess.run(
            ["docker", "compose", "up", "-d", "--quiet-pull"],
            cwd=ROOT, check=True, capture_output=True
        )
    except subprocess.CalledProcessError:
        # Starszy docker-compose (v1)
        try:
            subprocess.run(
                ["docker-compose", "up", "-d", "--quiet-pull"],
                cwd=ROOT, check=True, capture_output=True
            )
        except subprocess.CalledProcessError:
            return False

    print("  Czekam aż MongoDB się uruchomi...")
    for _ in range(15):
        time.sleep(2)
        if _mongo_is_running():
            return True
    return False


def _start_via_mongod() -> bool:
    """Spróbuj uruchomić systemowe mongod."""
    if not shutil.which("mongod"):
        return False
    print("  Uruchamiam systemowe mongod...")
    try:
        subprocess.Popen(
            ["mongod", "--quiet"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        for _ in range(10):
            time.sleep(1)
            if _mongo_is_running():
                return True
    except Exception:
        pass
    return False


def ensure_mongodb():
    step(2, 6, "Sprawdzam MongoDB...")

    if _mongo_is_running():
        print(green("  ✓ MongoDB już działa na localhost:27017"))
        return

    print(yellow("  MongoDB nie jest uruchomione. Próbuję uruchomić..."))

    if _start_via_docker():
        print(green("  ✓ MongoDB uruchomione przez Docker"))
        return

    if _start_via_mongod():
        print(green("  ✓ MongoDB uruchomione (systemowe mongod)"))
        return

    print(red("\n  BŁĄD: Nie mogę uruchomić MongoDB."))
    print("  Zainstaluj jedną z opcji:")
    print("    • Docker Desktop: https://www.docker.com/products/docker-desktop/")
    print("    • MongoDB Community: https://www.mongodb.com/try/download/community")
    print("  Następnie uruchom ponownie ten skrypt.")
    sys.exit(1)


# ─── Konfiguracja ────────────────────────────────────────────────

def write_config():
    step(3, 6, "Tworzę konfigurację lokalną...")
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)

    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            existing = json.load(f)
        if "localhost" in existing.get("mongodb_uri", ""):
            print(green("  ✓ config.json już wskazuje na localhost – pomijam"))
            return
        print(yellow("  Nadpisuję istniejący config.json (stary wskazywał na Atlas)"))

    config = {
        "mongodb_uri":      MONGO_URI,
        "mongodb_db":       MONGO_DB,
        "user_id":          USER_ID,
        "sync_interval_sec": 60,
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(green(f"  ✓ Zapisano {CONFIG_PATH}"))


# ─── Seed ────────────────────────────────────────────────────────

def seed_database():
    step(4, 6, "Seeduję bazę danych...")
    if not os.path.exists(SEED_SCRIPT):
        print(yellow(f"  Brak {SEED_SCRIPT} – pomijam seedowanie"))
        return
    result = subprocess.run(
        [sys.executable, SEED_SCRIPT, "--uri", MONGO_URI, "--db", MONGO_DB],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        for line in result.stdout.strip().splitlines():
            print(f"  {green('✓')} {line}")
    else:
        print(yellow(f"  Ostrzeżenie podczas seedowania:\n{result.stderr}"))


# ─── Rozszerzenie Chrome ──────────────────────────────────────────

def build_docs():
    step(5, 6, "Buduję dokumentację Sphinx...")
    if not os.path.exists(DOCS_DIR):
        print(yellow("  Brak katalogu docs/ – pomijam"))
        return

    # Upewnij się, że sphinx i motyw są zainstalowane
    sphinx_missing = []
    for pkg in ("sphinx", "sphinx_rtd_theme"):
        try:
            __import__(pkg)
        except ImportError:
            sphinx_missing.append(pkg)

    if sphinx_missing:
        print(yellow(f"  Instaluję: {', '.join(sphinx_missing)}..."))
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"] + sphinx_missing + ["--quiet"]
            )
        except subprocess.CalledProcessError:
            print(yellow("  Nie udało się zainstalować Sphinx – pomijam dokumentację"))
            return

    build_dir = os.path.join(DOCS_DIR, "_build", "html")
    result = subprocess.run(
        [sys.executable, "-m", "sphinx", "-M", "html", DOCS_DIR, os.path.join(DOCS_DIR, "_build"), "-q"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(green(f"  ✓ Dokumentacja zbudowana → {build_dir}"))
        print(f"  Otwórz: {bold(os.path.join(build_dir, 'index.html'))}")
    else:
        # Sphinx wypisuje ostrzeżenia na stderr; ignoruj niefatalne
        lines = (result.stderr or result.stdout).strip().splitlines()
        errors = [l for l in lines if "ERROR" in l or "Exception" in l]
        if errors:
            print(yellow(f"  Ostrzeżenia Sphinx (dokumentacja może być niekompletna):"))
            for l in errors[:5]:
                print(f"    {l}")
        else:
            print(green(f"  ✓ Dokumentacja zbudowana → {build_dir}"))


def print_extension_instructions():
    step(6, 6, "Rozszerzenie Chrome")
    ext_abs = os.path.abspath(EXTENSION_PATH)

    print(f"""
  Rozszerzenie {bold('nie może być zainstalowane automatycznie')} (ograniczenie Chrome).
  Wykonaj poniższe kroki {bold('raz')}:

  1. Otwórz Chrome i przejdź do:
     {bold('chrome://extensions')}

  2. Włącz {bold('Tryb dewelopera')} (przełącznik w prawym górnym rogu)

  3. Kliknij {bold('Załaduj rozpakowane')}

  4. Wskaż folder:
     {bold(ext_abs)}

  5. Gotowe – ikona Time Guard pojawi się na pasku przeglądarki.

  {yellow('Ważne:')} Rozszerzenie działa tylko gdy aplikacja główna (main.py) jest uruchomiona.
""")


# ─── Main ────────────────────────────────────────────────────────

def main():
    print(bold("\n╔══════════════════════════════════╗"))
    print(bold("║   Time Guard – Setup środowiska  ║"))
    print(bold("╚══════════════════════════════════╝"))

    ensure_dependencies()
    ensure_mongodb()
    write_config()
    seed_database()
    build_docs()
    print_extension_instructions()

    print(bold("─" * 45))
    print(green("  Setup zakończony pomyślnie!"))
    print(f"  Uruchom aplikację:  {bold('python main.py')}")
    print(bold("─" * 45) + "\n")


if __name__ == "__main__":
    main()
