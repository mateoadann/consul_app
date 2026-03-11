"""replace telefono with cumpleanos

Revision ID: cdc2776fae42
Revises: 7a8b9c0d1e2f
Create Date: 2026-03-11 12:15:53.254455

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'cdc2776fae42'
down_revision = '7a8b9c0d1e2f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('pacientes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cumpleanos', sa.Date(), nullable=True))
        batch_op.drop_column('telefono')


def downgrade():
    with op.batch_alter_table('pacientes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('telefono', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
        batch_op.drop_column('cumpleanos')
