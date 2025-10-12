from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "967cefbfcf70"
down_revision = "xxxx_add_contact_notes"   # <- deja el id correcto de la migración anterior
branch_labels = None
depends_on = None


def upgrade():
    # 1) Añadir la columna al final (SQLite lo permite sin recrear la tabla).
    op.add_column("client", sa.Column("provider_id", sa.Integer(), nullable=True))

    # 2) Crear la FK con nombre explícito.
    op.create_foreign_key(
        "fk_client_provider",        # NOMBRE OBLIGATORIO
        "client",                    # tabla hija
        "provider",                  # tabla padre
        ["provider_id"],             # columnas hijas
        ["id"],                      # columnas padre
        ondelete="SET NULL"
    )


def downgrade():
    # Quitar FK y columna en orden inverso
    op.drop_constraint("fk_client_provider", "client", type_="foreignkey")
    op.drop_column("client", "provider_id")
