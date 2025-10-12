# app/__init__.py
import os
from urllib.parse import urlparse

from flask import Flask
from config import Config
from .extensions import db, migrate, login_manager

# Blueprints
from .blueprints.auth import auth_bp
from .blueprints.core import core_bp
from .blueprints.providers import providers_bp
from .blueprints.clients import clients_bp
from .blueprints.accounts import accounts_bp

# Notificaciones (scheduler opcional)
from apscheduler.schedulers.background import BackgroundScheduler
from .services.notify import send_pushover_now

# Evitamos múltiples schedulers en procesos/instancias
scheduler = None


def _ensure_dirs(app: Flask) -> None:
    """Crea carpetas necesarias en runtime (uploads, instance y /data para SQLite en Fly)."""
    # uploads
    os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)

    # instance
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # /data (si DATABASE_URL apunta a /data: SQLite en volumen de Fly)
    db_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    try:
        parsed = urlparse(db_url)
        # ej: sqlite:////data/app.sqlite -> path "/data/app.sqlite"
        if parsed.scheme.startswith("sqlite") and parsed.path and parsed.path.startswith("/data/"):
            os.makedirs("/data", exist_ok=True)
    except Exception:
        # no interrumpir arranque por esto
        pass


def _run_db_migrations_on_start(app):
    # solo corre si existe migrations/env.py y si RUN_AUTOMIGRATE=1
    if os.environ.get("RUN_AUTOMIGRATE") != "1":
        return
    mig_dir = os.path.join(app.root_path, "..", "migrations")
    if not os.path.exists(os.path.join(mig_dir, "env.py")):
        app.logger.warning("Skipping auto-migrate: migrations/env.py not found")
        return
    from flask_migrate import upgrade
    with app.app_context():
        upgrade(directory=mig_dir)


def _start_scheduler_if_enabled(app: Flask) -> None:
    """Inicia APScheduler para notificaciones si está habilitado en Config + ENV."""
    # ENABLE_SCHEDULER (Config) habilita característica.
    # RUN_SCHEDULER (ENV) evita múltiples schedulers al escalar (solo una instancia con "1").
    if not app.config.get("ENABLE_SCHEDULER", True):
        app.logger.info("ENABLE_SCHEDULER desactivado: no se inicia APScheduler.")
        return

    if os.environ.get("RUN_SCHEDULER", "1") != "1":
        app.logger.info("RUN_SCHEDULER != '1': no se inicia APScheduler en esta instancia.")
        return

    global scheduler
    if scheduler is not None:
        app.logger.info("APScheduler ya estaba iniciado; no se duplica.")
        return

    hour = int(app.config.get("NOTIFY_RUN_HOUR", 9))
    s = BackgroundScheduler(daemon=True)
    s.add_job(
        func=lambda: _run_notify_job(app),
        trigger="cron",
        hour=hour,
        minute=0,
        id="notify_daily",
        replace_existing=True,
    )
    s.start()
    scheduler = s
    app.logger.info("APScheduler iniciado: job 'notify_daily' a las %02d:00", hour)


def _run_notify_job(app: Flask) -> None:
    """Job que envía el resumen por Pushover."""
    with app.app_context():
        try:
            results = send_pushover_now()  # usa current_app/config internamente
            app.logger.info("Pushover notifications enviadas: %s", results)
        except Exception as e:
            app.logger.exception("Notifier error: %s", e)


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Carpetas necesarias (uploads, instance, /data si corresponde)
    _ensure_dirs(app)

    # Extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(providers_bp, url_prefix="/providers")
    app.register_blueprint(clients_bp, url_prefix="/clients")
    app.register_blueprint(accounts_bp, url_prefix="/accounts")

    # Migraciones en arranque (soluciona el problema del release_command con SQLite en Fly)
    _run_db_migrations_on_start(app)

    # Scheduler diario (Pushover), si procede
    _start_scheduler_if_enabled(app)

    return app
