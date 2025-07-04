"""Merge heads, keep 63d87c70cfd0

Revision ID: e20d2d846292
Revises: 63d87c70cfd0_fix_difficulty_lowercase, xxx_fix_difficulty_data
Create Date: 2025-07-04 17:53:36.374541

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e20d2d846292'
down_revision: Union[str, None] = ('63d87c70cfd0_fix_difficulty_lowercase', 'xxx_fix_difficulty_data')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
