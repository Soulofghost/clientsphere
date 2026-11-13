import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = os.getenv("CLIENTSPHERE_DB", str(DATA_DIR / "clientsphere.db"))
PORT = int(os.getenv("PORT", "8005"))
API_PREFIX = "/api/v1"
