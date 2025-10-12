import os

basedir = os.path.abspath(os.path.dirname(__file__))

def _bool(key, default="0"):
    return os.environ.get(key, default) == "1"

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-this")

    # Dir persistente en Fly
    DATA_DIR = os.environ.get("DATA_DIR", os.path.join(basedir, "instance"))
    os.makedirs(DATA_DIR, exist_ok=True)

    # DB: toma DATABASE_URL si existe; si no, usa sqlite en /data/app.sqlite
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(DATA_DIR, 'app.sqlite')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ALLOW_REGISTRATION = _bool("ALLOW_REGISTRATION", "1")
    # Cargas subidas: en DATA_DIR para ser persistentes
    UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # --- Notificaciones (Pushover) ---
    ENABLE_SCHEDULER = _bool("ENABLE_SCHEDULER", "1")
    NOTIFY_WINDOW_DAYS = int(os.environ.get("NOTIFY_WINDOW_DAYS", "7"))
    NOTIFY_RUN_HOUR = int(os.environ.get("NOTIFY_RUN_HOUR", "9"))

    PUSHOVER_USER_KEY = os.environ.get("PUSHOVER_USER_KEY")
    PUSHOVER_API_TOKEN = os.environ.get("PUSHOVER_API_TOKEN")

    # Formato / límites
    NOTIFY_INCLUDE_PASSWORDS = _bool("NOTIFY_INCLUDE_PASSWORDS", "0")
    NOTIFY_MAX_ITEMS_PER_SECTION = int(os.environ.get("NOTIFY_MAX_ITEMS_PER_SECTION", "8"))
    NOTIFY_MESSAGE_CHAR_LIMIT = int(os.environ.get("NOTIFY_MESSAGE_CHAR_LIMIT", "1000"))
