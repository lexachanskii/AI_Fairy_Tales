"""add tale hero and moral

Revision ID: c3d4e5f6a7b8
Revises: b2f3d4e5f6a7
Create Date: 2026-04-30 15:30:00.000000

Adds optional fields used by the web tale setup form and by the prompt context.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2f3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tales", sa.Column("hero", sa.String(length=500), nullable=True))
    op.add_column("tales", sa.Column("moral", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("tales", "moral")
    op.drop_column("tales", "hero")
