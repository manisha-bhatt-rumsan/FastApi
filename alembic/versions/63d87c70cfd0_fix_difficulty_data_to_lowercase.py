"""Fix difficulty data to lowercase

Revision ID: xxx_fix_difficulty_lowercase
Revises: 588e8fa12b62
Create Date: 2025-07-04
"""

from alembic import op

revision = '63d87c70cfd0_fix_difficulty_lowercase'
down_revision = '588e8fa12b62'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("UPDATE questions SET difficulty = LOWER(difficulty) WHERE difficulty IN ('EASY', 'MEDIUM', 'HARD')")

def downgrade():
    op.execute("UPDATE questions SET difficulty = UPPER(difficulty) WHERE difficulty IN ('easy', 'medium', 'hard')")