"""add status_manual to Account"""

from alembic import op
import sqlalchemy as sa

# Reemplaza por los tuyos si no coinciden:
revision = "29a460bb501b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Solo añadimos la columna; evitamos otros cambios autogenerados.
    with op.batch_alter_table("account") as batch_op:
        batch_op.add_column(sa.Column("status_manual", sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table("account") as batch_op:
        batch_op.drop_column("status_manual")
