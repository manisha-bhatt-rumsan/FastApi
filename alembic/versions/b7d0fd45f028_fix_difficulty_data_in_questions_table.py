"""Fix difficulty data in questions table

Revision ID: xxx_fix_difficulty_data
Revises: 588e8fa12b62
Create Date: 2025-07-04
"""

from alembic import op

revision = 'xxx_fix_difficulty_data'
down_revision = '588e8fa12b62'
branch_labels = None
depends_on = None

def upgrade():
    op.execute("UPDATE questions SET difficulty = UPPER(difficulty) WHERE difficulty IN ('Easy', 'Medium', 'Hard')")

def downgrade():
    op.execute("UPDATE questions SET difficulty = INITCAP(difficulty) WHERE difficulty IN ('EASY', 'MEDIUM', 'HARD')")