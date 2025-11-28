"""remove created_by from tool_definitions

Revision ID: 6418537daf9b
Revises: d2b1e36354cf
Create Date: 2025-11-26 16:59:39.717622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6418537daf9b'
down_revision: Union[str, None] = 'd2b1e36354cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove created_by from tool_definition_revisions
    op.drop_constraint('tool_definition_revisions_created_by_fkey', 'tool_definition_revisions', type_='foreignkey')
    op.drop_column('tool_definition_revisions', 'created_by')

    # Remove created_by from tool_definitions
    op.drop_constraint('tool_definitions_created_by_fkey', 'tool_definitions', type_='foreignkey')
    op.drop_column('tool_definitions', 'created_by')


def downgrade() -> None:
    """Downgrade schema."""
    # Re-add created_by to tool_definitions
    op.add_column('tool_definitions', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_foreign_key('tool_definitions_created_by_fkey', 'tool_definitions', 'users', ['created_by'], ['id'], ondelete='CASCADE')

    # Re-add created_by to tool_definition_revisions
    op.add_column('tool_definition_revisions', sa.Column('created_by', sa.UUID(), nullable=True))
    op.create_foreign_key('tool_definition_revisions_created_by_fkey', 'tool_definition_revisions', 'users', ['created_by'], ['id'], ondelete='CASCADE')
