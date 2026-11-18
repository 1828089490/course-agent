"""create papers and chunks tables

Revision ID: 418bec572406
Revises: 
Create Date: 2026-11-17 20:43:12.302217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '418bec572406'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""
        CREATE TABLE papers (
            id BIGSERIAL PRIMARY KEY,
            arxiv_id TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            authors TEXT[] NOT NULL,
            abstract TEXT NOT NULL,
            categories TEXT[] NOT NULL,
            published_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            doi TEXT,
            journal_ref TEXT,
            pdf_url TEXT NOT NULL,
            added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            ingest_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (ingest_status IN ('pending', 'ready', 'failed'))
        )
    """)
    op.execute("""
        CREATE TABLE chunks (
            id BIGSERIAL PRIMARY KEY,
            paper_id BIGINT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            section TEXT,
            page INTEGER,
            content TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            embedding vector(1536),
            UNIQUE (paper_id, chunk_index)
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE chunks")
    op.execute("DROP TABLE papers")
