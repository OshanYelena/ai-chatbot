"""add database indexes

Revision ID: 2ab3d33df443
Revises: 325ff7eac7a2
Create Date: 2026-04-29 11:13:50.318310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ab3d33df443'
down_revision: Union[str, Sequence[str], None] = '325ff7eac7a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op

def upgrade() -> None:

    op.create_index(

        "idx_conversations_user_id",

        "conversations",

        ["user_id"],

    )

    op.create_index(

        "idx_chat_messages_conversation_id",

        "chat_messages",

        ["conversation_id"],

    )

    op.create_index(

        "idx_chat_messages_created_at",

        "chat_messages",

        ["created_at"],

    )

    op.create_index(

        "idx_long_term_memories_user_id",

        "long_term_memories",

        ["user_id"],

    )

    op.create_index(

        "idx_long_term_memories_user_key",

        "long_term_memories",

        ["user_id", "key"],

    )

    op.create_index(

        "idx_pending_conflicts_conversation_status",

        "pending_memory_conflicts",

        ["conversation_id", "status"],

    )

def downgrade() -> None:

    op.drop_index("idx_pending_conflicts_conversation_status", table_name="pending_memory_conflicts")

    op.drop_index("idx_long_term_memories_user_key", table_name="long_term_memories")

    op.drop_index("idx_long_term_memories_user_id", table_name="long_term_memories")

    op.drop_index("idx_chat_messages_created_at", table_name="chat_messages")

    op.drop_index("idx_chat_messages_conversation_id", table_name="chat_messages")

    op.drop_index("idx_conversations_user_id", table_name="conversations")