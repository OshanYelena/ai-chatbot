from app.repositories.conversation_repository import ConversationRepository


class LongTermMemoryService:
    def get_memory(
        self,
        repo: ConversationRepository,
        conversation_id: str,
    ) -> dict:
        return repo.get_long_term_memory(conversation_id)

    def update_memory(
        self,
        repo: ConversationRepository,
        conversation_id: str,
        key: str,
        value: str,
    ):
        repo.upsert_long_term_memory(
            conversation_id=conversation_id,
            key=key,
            value=value,
        )

    def format_memory_for_prompt(
        self,
        repo: ConversationRepository,
        conversation_id: str,
    ) -> str:
        memory = self.get_memory(repo, conversation_id)

        if not memory:
            return ""

        formatted = "\n".join(
            [f"{key}: {value}" for key, value in memory.items()]
        )

        return f"User known facts:\n{formatted}"


long_term_memory_service = LongTermMemoryService()