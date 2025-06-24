"""Add question_type enum

Revision ID: d7be7699a9f9
Revises: ef7e49627b14
Create Date: 2025-06-24 11:06:37.360544

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd7be7699a9f9'
down_revision: Union[str, None] = 'ef7e49627b14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE TYPE question_type AS ENUM ('mcq', 'faq', 'boolean')")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TYPE question_type")
    pass
