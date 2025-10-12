# app/models.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

# -----------------------
# Usuario (autenticación)
# -----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


# -----------------------
# Proveedor / Cliente
# -----------------------
class Provider(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)

    # Relación inversa explícita (evita colisiones de backref)
    accounts = db.relationship(
        "Account",
        back_populates="provider",
        cascade="all, delete-orphan"
    )


class Client(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(255), unique=True, nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey("provider.id"))
    provider    = db.relationship("Provider")

    accounts = db.relationship(
        "Account",
        back_populates="client",
        cascade="all, delete-orphan"
    )


# -----------------------
# Cuenta de plataforma
# -----------------------
class Account(db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(255), nullable=False)  # correo
    password = db.Column(db.String(255))
    notes    = db.Column(db.Text)

    start_date     = db.Column(db.Date)
    end_date       = db.Column(db.Date)
    time_allocated = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    provider_id = db.Column(db.Integer, db.ForeignKey("provider.id"))
    client_id   = db.Column(db.Integer, db.ForeignKey("client.id"))

    # Relaciones sin backref; usan back_populates para evitar conflicto
    provider = db.relationship("Provider", back_populates="accounts")
    client   = db.relationship("Client",   back_populates="accounts")

    # Estado manual opcional: None | 'CAIDA'
    status_manual = db.Column(db.String(20), nullable=True)


# Export explícito (opcional, pero ayuda a evitar confusiones)
__all__ = ["User", "Provider", "Client", "Account"]
