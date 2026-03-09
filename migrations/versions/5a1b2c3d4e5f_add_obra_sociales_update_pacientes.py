"""add obra_sociales table and update pacientes fields

Revision ID: 5a1b2c3d4e5f
Revises: 4c9d2e3f1a0b
Create Date: 2026-03-09 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a1b2c3d4e5f'
down_revision = '4c9d2e3f1a0b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('obra_sociales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )

    with op.batch_alter_table('pacientes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('apodo', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('numero_afiliado', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('obra_social_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_pacientes_obra_social_id', 'obra_sociales', ['obra_social_id'], ['id'])
        batch_op.drop_column('email')
        batch_op.drop_column('obra_social')


def downgrade():
    with op.batch_alter_table('pacientes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('obra_social', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('email', sa.String(length=120), nullable=True))
        batch_op.drop_constraint('fk_pacientes_obra_social_id', type_='foreignkey')
        batch_op.drop_column('obra_social_id')
        batch_op.drop_column('numero_afiliado')
        batch_op.drop_column('apodo')

    op.drop_table('obra_sociales')
