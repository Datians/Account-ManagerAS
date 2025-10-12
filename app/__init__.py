# app/__init__.py
import os
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

scheduler = None

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Carpetas necesarias
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

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

    # Scheduler diario (si está habilitado en .env)
    if app.config.get("ENABLE_SCHEDULER", True):
        global scheduler
        if scheduler is None:
            scheduler = BackgroundScheduler(daemon=True)
            hour = int(app.config.get("NOTIFY_RUN_HOUR", 9))
            scheduler.add_job(
                func=lambda: _run_notify_job(app),
                trigger="cron",
                hour=hour,
                minute=0,
                id="notify_daily",
                replace_existing=True,
            )
            scheduler.start()

    return app

def _run_notify_job(app):
    """Job que envía el resumen por Pushover."""
    with app.app_context():
        try:
            results = send_pushover_now()  # <- usa la función correcta
            app.logger.info("Pushover notifications: %s", results)
        except Exception as e:
            app.logger.exception("Notifier error: %s", e)
