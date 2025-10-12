from app import create_app
from app.extensions import db
# 👇 IMPORTANTE: importa los modelos para que SQLAlchemy registre las tablas
import app.models  # noqa: F401

app = create_app()
with app.app_context():
    db.create_all()
    print("✅ Database initialized (tablas creadas).")
