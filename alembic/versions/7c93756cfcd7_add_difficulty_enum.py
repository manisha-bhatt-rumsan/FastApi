"""Add difficulty enum

Revision ID: 7c93756cfcd7
Revises: d7be7699a9f9
Create Date: 2025-07-02 14:59:55.505773
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import VARCHAR

# revision identifiers, used by Alembic.
revision: str = '7c93756cfcd7'
down_revision: Union[str, None] = 'd7be7699a9f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Create ENUM type for difficulty
    difficulty_enum = sa.Enum("Easy", "Medium", "Hard", name="difficulty_level")
    difficulty_enum.create(op.get_bind())

    # Apply other schema changes
    op.alter_column('documents', 'content',
               existing_type=postgresql.BYTEA(),
               type_=sa.Text(),
               existing_nullable=True)

    op.drop_column('documents', 'file_name')

    op.alter_column('questions', 'question',
               existing_type=sa.VARCHAR(),
               type_=sa.Text(),
               existing_nullable=False)

    # Update null difficulty values to 'Medium' to prevent NOT NULL errors
    op.execute("UPDATE questions SET difficulty='Medium' WHERE difficulty IS NULL")

    op.alter_column('questions', 'difficulty',
               existing_type=sa.VARCHAR(),
               type_=sa.Enum("Easy", "Medium", "Hard", name="difficulty_level"),
               nullable=False)

    op.alter_column('questions', 'correct_answer',
               existing_type=sa.VARCHAR(),
               type_=sa.Text(),
               existing_nullable=False)

    op.alter_column('questions', 'explanation',
               existing_type=sa.VARCHAR(),
               type_=sa.Text(),
               existing_nullable=True)

    op.drop_constraint(op.f('quizzes_document_id_fkey'), 'quizzes', type_='foreignkey')
    op.drop_column('quizzes', 'document_id')


def downgrade() -> None:
    """Downgrade schema."""

    op.add_column('quizzes', sa.Column('document_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key(op.f('quizzes_document_id_fkey'), 'quizzes', 'documents', ['document_id'], ['id'])

    op.alter_column('questions', 'explanation',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(),
               existing_nullable=True)

    op.alter_column('questions', 'correct_answer',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(),
               existing_nullable=False)

    op.alter_column('questions', 'difficulty',
               existing_type=sa.Enum("Easy", "Medium", "Hard", name="difficulty_level"),
               type_=sa.VARCHAR(),
               nullable=True)

    op.alter_column('questions', 'question',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(),
               existing_nullable=False)

    op.add_column('documents', sa.Column('file_name', sa.VARCHAR(), autoincrement=False, nullable=False))

    op.alter_column('documents', 'content',
               existing_type=sa.Text(),
               type_=postgresql.BYTEA(),
               existing_nullable=True)

    # Drop ENUM type
    difficulty_enum = sa.Enum("Easy", "Medium", "Hard", name="difficulty_level")
    difficulty_enum.drop(op.get_bind())
