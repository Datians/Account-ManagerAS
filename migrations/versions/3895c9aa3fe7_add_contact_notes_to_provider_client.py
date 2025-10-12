from alembic import op
import sqlalchemy as sa

revision = "xxxx_add_contact_notes"
down_revision = "3895c9aa3fe7"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("provider", sa.Column("contact", sa.String(255), nullable=True))
    op.add_column("provider", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("client", sa.Column("contact", sa.String(255), nullable=True))
    op.add_column("client", sa.Column("notes", sa.Text(), nullable=True))

def downgrade():
    op.drop_column("client", "notes")
    op.drop_column("client", "contact")
    op.drop_column("provider", "notes")
    op.drop_column("provider", "contact")
