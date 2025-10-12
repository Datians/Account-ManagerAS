import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-this")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(basedir, 'instance', 'app.sqlite')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALLOW_REGISTRATION = os.environ.get("ALLOW_REGISTRATION", "1") == "1"
    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # --- Notificaciones (Pushover) ---
    ENABLE_SCHEDULER = os.environ.get("ENABLE_SCHEDULER", "1") == "1"
    NOTIFY_WINDOW_DAYS = int(os.environ.get("NOTIFY_WINDOW_DAYS", "7"))
    NOTIFY_RUN_HOUR = int(os.environ.get("NOTIFY_RUN_HOUR", "9"))

    PUSHOVER_USER_KEY = os.environ.get("PUSHOVER_USER_KEY")
    PUSHOVER_API_TOKEN = os.environ.get("PUSHOVER_API_TOKEN")

    # Formato / límites
    NOTIFY_INCLUDE_PASSWORDS = os.environ.get("NOTIFY_INCLUDE_PASSWORDS", "0") == "1"
    NOTIFY_MAX_ITEMS_PER_SECTION = int(os.environ.get("NOTIFY_MAX_ITEMS_PER_SECTION", "8"))
    NOTIFY_MESSAGE_CHAR_LIMIT = int(os.environ.get("NOTIFY_MESSAGE_CHAR_LIMIT", "1000"))

        # Opcional: URL base para links (para abrir “Editar cuenta” desde el push)
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000")

    # Pushover visual: sonidos/priority por tipo
    PUSHOVER_DEVICE = os.environ.get("PUSHOVER_DEVICE")  # opcional
    PUSH_SUMMARY_SOUND = os.environ.get("PUSH_SUMMARY_SOUND", "magic")
    PUSH_TODAY_SOUND   = os.environ.get("PUSH_TODAY_SOUND", "siren")
    PUSH_SOON_SOUND    = os.environ.get("PUSH_SOON_SOUND", "echo")
    PUSH_TODAY_PRIORITY = int(os.environ.get("PUSH_TODAY_PRIORITY", "1"))   # 1 = alta
    PUSH_OTHER_PRIORITY = int(os.environ.get("PUSH_OTHER_PRIORITY", "0"))   # 0 = normal

    # Agrupar por proveedor (mejor lectura cuando hay muchas)
    NOTIFY_GROUP_BY_PROVIDER = os.environ.get("NOTIFY_GROUP_BY_PROVIDER", "1") == "1"

    # Adjuntar gráfico PNG en el resumen (sí/no)
    NOTIFY_ATTACH_CHART = os.environ.get("NOTIFY_ATTACH_CHART", "0") == "1"
