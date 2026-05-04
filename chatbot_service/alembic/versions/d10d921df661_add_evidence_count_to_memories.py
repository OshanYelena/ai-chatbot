"""add evidence count to memories

Revision ID: d10d921df661
Revises: 897b21f163a7
Create Date: 2026-04-29 12:31:28.551087

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd10d921df661'
down_revision: Union[str, Sequence[str], None] = '897b21f163a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column(

        "long_term_memories",

        sa.Column("evidence_count", sa.Integer(), nullable=True),

    )

    op.execute("""

        UPDATE long_term_memories

        SET evidence_count = 1

        WHERE evidence_count IS NULL

    """)

    op.alter_column(

        "long_term_memories",

        "evidence_count",

        nullable=False,

    )

def downgrade() -> None:

    op.drop_column("long_term_memories", "evidence_count")