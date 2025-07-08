"""Updated questions table

Revision ID: ef7e49627b14
Revises: 2296464b3006
Create Date: 2025-06-23 21:33:45.498202

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'ef7e49627b14'
down_revision: Union[str, None] = '2296464b3006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('questions', sa.Column('question', sa.Text(), nullable=False))
    op.add_column('questions', sa.Column('type', sa.VARCHAR(7), nullable=False))
    op.add_column('questions', sa.Column('choices', sa.ARRAY(sa.String()), nullable=True))
    op.add_column('questions', sa.Column('correct_answer', sa.Text(), nullable=False))
    op.add_column('questions', sa.Column('explanation', sa.Text(), nullable=True))
    op.drop_column('questions', 'text')

def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('questions', sa.Column('text', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_column('questions', 'explanation')
    op.drop_column('questions', 'correct_answer')
    op.drop_column('questions', 'choices')
    op.drop_column('questions', 'type')
    op.drop_column('questions', 'question')