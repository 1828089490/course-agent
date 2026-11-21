"""chunks: page to page_start and page_end

Revision ID: e73f5e08851d
Revises: 418bec572406
Create Date: 2026-11-20 20:50:23.883760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e73f5e08851d'
down_revision: Union[str, Sequence[str], None] = '418bec572406'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TABLE chunks RENAME COLUMN page TO page_start")
    op.execute("ALTER TABLE chunks ADD COLUMN page_end INTEGER")
    op.execute("""
        ALTER TABLE chunks ADD CONSTRAINT chunks_page_range
            CHECK (page_end >= page_start)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE chunks DROP COLUMN page_end")
    op.execute("ALTER TABLE chunks RENAME COLUMN page_start TO page")