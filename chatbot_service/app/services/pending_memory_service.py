from typing import Dict, List

from app.repositories.conversation_repository import ConversationRepository


class PendingMemoryService:

    def set_pending_conflicts(

        self,

        repo: ConversationRepository,

        user_id: str,

        conversation_id: str,

        conflicts: list[dict],

    ):

        repo.create_pending_memory_conflicts(

            user_id=user_id,

            conversation_id=conversation_id,

            conflicts=conflicts,

        )

    def get_pending_conflicts(

        self,

        repo: ConversationRepository,

        conversation_id: str,

    ) -> list[dict]:

        conflicts = repo.get_pending_memory_conflicts(conversation_id)

        return [

            {

                "key": conflict.key,

                "old_value": conflict.old_value,

                "new_value": conflict.new_value,

            }

            for conflict in conflicts

        ]

    def clear_pending_conflicts(

        self,

        repo: ConversationRepository,

        conversation_id: str,

        status: str,

    ):

        repo.resolve_pending_memory_conflicts(

            conversation_id=conversation_id,

            status=status,

        )


pending_memory_service = PendingMemoryService()