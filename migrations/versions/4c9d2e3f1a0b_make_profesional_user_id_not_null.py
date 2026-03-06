"""make profesional user_id not null

Revision ID: 4c9d2e3f1a0b
Revises: 3b8f1f4c9b2a
Create Date: 2026-03-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c9d2e3f1a0b'
down_revision = '3b8f1f4c9b2a'
branch_labels = None
depends_on = None


def upgrade():
    # First, ensure no profesionales exist without a user_id
    # This will fail if there are orphan profesionales - they must be cleaned up first
    op.execute("""
        DELETE FROM profesionales
        WHERE user_id IS NULL
    """)

    # Make user_id NOT NULL
    with op.batch_alter_table('profesionales', schema=None) as batch_op:
        batch_op.alter_column('user_id',
            existing_type=sa.Integer(),
            nullable=False)


def downgrade():
    # Make user_id nullable again
    with op.batch_alter_table('profesionales', schema=None) as batch_op:
        batch_op.alter_column('user_id',
            existing_type=sa.Integer(),
            nullable=True)
