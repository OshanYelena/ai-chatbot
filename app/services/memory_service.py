from typing import List

from app.core.config import settings
from app.db.models import LongTermMemory
from app.repositories.conversation_repository import ConversationRepository


class MemoryService:
    def get_or_create_conversation(
        self,
        repo: ConversationRepository,
        user_id: str,
        conversation_id: str | None,
    ) -> str:
        conversation = repo.get_or_create_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        return conversation.id

    def add_message(
        self,
        repo: ConversationRepository,
        conversation_id: str,
        role: str,
        content: str,
    ):
        repo.add_message(conversation_id, role, content)

    def get_messages(
        self,
        repo: ConversationRepository,
        conversation_id: str,
    ) -> List[dict]:
        messages = repo.get_messages(conversation_id)

        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

    def should_summarize(
        self,
        repo: ConversationRepository,
        conversation_id: str,
    ) -> bool:
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
        user_id: str,
        conversation_id: str,
    ) -> List[dict]:
        messages: List[dict] = []

        long_term_memory = repo.get_long_term_memory(user_id)

        high_conf = []

        medium_conf = []

        low_conf = []

        for key, value in long_term_memory.items():

            memory = (

                repo.db.query(LongTermMemory)

                .filter(

                    LongTermMemory.user_id == user_id,

                    LongTermMemory.key == key,

                )

                .first()

            )

            if not memory:
                continue

            if memory.confidence == "high":

                high_conf.append(f"{key}: {value}")

            elif memory.confidence == "medium":

                medium_conf.append(f"{key}: {value}")

            else:

                low_conf.append(f"{key}: {value}")

        if high_conf:
            messages.append({

                "role": "system",

                "content": "User confirmed facts:\n" + "\n".join(high_conf),

            })

        if medium_conf:
            messages.append({

                "role": "system",

                "content": "User likely facts:\n" + "\n".join(medium_conf),

            })

        if low_conf:
            messages.append({

                "role": "system",

                "content": (

                        "Uncertain user information (may be outdated or incorrect):\n"

                        + "\n".join(low_conf)

                ),

            })



        structured_memory = {
            k: v for k, v in long_term_memory.items() if not k.startswith("dynamic_")
        }

        dynamic_memory = {
            k: v for k, v in long_term_memory.items() if k.startswith("dynamic_")
        }

        if structured_memory:
            structured_text = "\n".join(
                [f"{k}: {v}" for k, v in structured_memory.items()]
            )

            messages.append({
                "role": "system",
                "content": f"User core facts:\n{structured_text}",
            })

        if dynamic_memory:
            dynamic_text = "\n".join(
                [f"{k}: {v}" for k, v in dynamic_memory.items()]
            )

            messages.append({
                "role": "system",
                "content": f"Additional user context:\n{dynamic_text}",
            })

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