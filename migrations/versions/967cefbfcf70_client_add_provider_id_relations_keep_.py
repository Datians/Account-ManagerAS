from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "967cefbfcf70"
down_revision = "xxxx_add_contact_notes"  # deja aquí el ID que ya tienes
branch_labels = None
depends_on = None


def upgrade():
    """
    Esta migración ya no hace nada porque la columna provider_id
    ya está incluida en el esquema inicial / migraciones anteriores.
    Solo dejamos el archivo para que Alembic pueda avanzar a esta revisión
    sin aplicar cambios de esquema.
    """
    pass


def downgrade():
    """
    Tampoco intentamos deshacer nada, porque no añadimos ni quitamos
    columnas en upgrade().
    """
    pass
