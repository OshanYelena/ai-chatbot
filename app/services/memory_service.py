from typing import List

from app.core.config import settings
from app.repositories.conversation_repository import ConversationRepository


class MemoryService:
    def get_or_create_conversation(self, repo: ConversationRepository, conversation_id: str | None) -> str:
        conversation = repo.get_or_create_conversation(conversation_id)
        return conversation.id

    def add_message(
        self,
        repo: ConversationRepository,
        conversation_id: str,
        role: str,
        content: str,
    ):
        repo.add_message(conversation_id, role, content)

    def get_messages(self, repo: ConversationRepository, conversation_id: str) -> List[dict]:
        messages = repo.get_messages(conversation_id)

        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

    def should_summarize(self, repo: ConversationRepository, conversation_id: str) -> bool:
        message_count = repo.get_message_count(conversation_id)
        return message_count >= settings.SUMMARY_TRIGGER_MESSAGES

    def compress_conversation(
        self,
        repo: ConversationRepository,
        conversation_id: str,
        summary: str,
    ):
        repo.update_summary(conversation_id, summary)
        repo.compress_conversation(
            conversation_id,
            settings.RECENT_MESSAGES_AFTER_SUMMARY,
        )

    def build_context_messages(
        self,
        repo: ConversationRepository,
        conversation_id: str,
    ) -> List[dict]:
        messages: List[dict] = []

        long_term_memory = repo.get_long_term_memory(conversation_id)

        if long_term_memory:
            memory_text = "\n".join(
                [f"{key}: {value}" for key, value in long_term_memory.items()]
            )

            messages.append(
                {
                    "role": "system",
                    "content": f"User known facts:\n{memory_text}",
                }
            )

        summary = repo.get_summary(conversation_id)

        if summary:
            messages.append(
                {
                    "role": "system",
                    "content": f"Previous conversation summary: {summary}",
                }
            )

        recent_messages = repo.get_recent_messages(
            conversation_id,
            settings.MAX_HISTORY_MESSAGES,
        )

        messages.extend(
            [
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in recent_messages
            ]
        )

        return messages


memory_service = MemoryService()