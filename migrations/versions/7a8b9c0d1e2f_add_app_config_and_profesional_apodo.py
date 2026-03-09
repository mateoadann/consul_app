"""add app_config table and profesional apodo

Revision ID: 7a8b9c0d1e2f
Revises: 5a1b2c3d4e5f
Create Date: 2026-03-09 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a8b9c0d1e2f'
down_revision = '5a1b2c3d4e5f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'app_config',
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('key'),
    )
    op.add_column('profesionales', sa.Column('apodo', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('profesionales', 'apodo')
    op.drop_table('app_config')
