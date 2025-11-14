from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers
revision = "967cefbfcf70"
down_revision = "3895c9aa3fe7_add_contact_notes_to_provider_client"  # <-- asegúrate que sea el ID REAL
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    """Devuelve True si la columna existe en la tabla."""
    bind = op.get_bind()
    insp = inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table_name)]
    return column_name in cols


def upgrade():
    # Solo añadir columna y FK si NO existe
    if not _has_column("client", "provider_id"):
        op.add_column(
            "client",
            sa.Column("provider_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_client_provider",
            "client",
            "provider",
            ["provider_id"],
            ["id"],
            ondelete="SET NULL",
        )
    # (no pasa nada si ya existe; simplemente no hace nada)


def downgrade():
    # Solo eliminar si existe
    if _has_column("client", "provider_id"):
        op.drop_constraint(
            "fk_client_provider",
            "client",
            type_="foreignkey",
        )
        op.drop_column("client", "provider_id")
