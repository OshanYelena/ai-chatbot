from app.repositories.conversation_repository import ConversationRepository


class LongTermMemoryService:
    def get_memory(
        self,
        repo: ConversationRepository,
        user_id: str,
    ) -> dict:
        return repo.get_long_term_memory(user_id)

    def update_memory(
            self,
            repo: ConversationRepository,
            user_id: str,
            key: str,
            value: str,
    ) -> dict:
        return repo.upsert_long_term_memory(
            user_id=user_id,
            key=key,
            value=value,
        )

    def format_memory_for_prompt(
        self,
        repo: ConversationRepository,
        user_id: str,
    ) -> str:
        memory = self.get_memory(repo, user_id)

        if not memory:
            return ""

        formatted = "\n".join(
            [f"{key}: {value}" for key, value in memory.items()]
        )

        return f"User known facts:\n{formatted}"

    def force_update_memory(
            self,
            repo: ConversationRepository,
            user_id: str,
            key: str,
            value: str,
    ) -> dict:
        return repo.force_update_long_term_memory(
            user_id=user_id,
            key=key,
            value=value,
        )


long_term_memory_service = LongTermMemoryService()