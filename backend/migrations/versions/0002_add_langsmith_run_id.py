"""add langsmith_run_id to chat_sessions

Revision ID: 0002_add_langsmith_run_id
Revises: 0001_init
Create Date: 2026-04-10
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_add_langsmith_run_id"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "chat_sessions",
        sa.Column("langsmith_run_id", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("chat_sessions", "langsmith_run_id")
