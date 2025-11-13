from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers
revision = "967cefbfcf70"
down_revision = "xxxx_add_contact_notes"  # ID correcto de la migración anterior
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('client')]

    # ✅ Solo añadir si no existe
    if 'provider_id' not in columns:
        op.add_column('client', sa.Column('provider_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_client_provider",
            "client",
            "provider",
            ["provider_id"],
            ["id"],
            ondelete="SET NULL"
        )
    else:
        print("🟡 La columna provider_id ya existe, se omite creación.")


def downgrade():
    # Revertir solo si la columna existe
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('client')]

    if 'provider_id' in columns:
        op.drop_constraint("fk_client_provider", "client", type_="foreignkey")
        op.drop_column("client", "provider_id")
