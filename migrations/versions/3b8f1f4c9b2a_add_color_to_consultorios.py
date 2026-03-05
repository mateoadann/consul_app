"""add color to consultorios

Revision ID: 3b8f1f4c9b2a
Revises: 8fd75e8a0d7b
Create Date: 2026-02-17 21:05:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3b8f1f4c9b2a"
down_revision = "8fd75e8a0d7b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "consultorios",
        sa.Column("color", sa.String(length=7), nullable=False, server_default="#EA8711"),
    )


def downgrade():
    op.drop_column("consultorios", "color")
