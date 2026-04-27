import uuid
from typing import Dict, List
from app.core.config import settings


class MemoryService:
    def __init__(self):
        self.store: Dict[str, List[dict]] = {}
        self.summaries: Dict[str, str] ={}

    def get_or_create_conversation(self, conversation_id : str | None) -> str:
        if conversation_id and conversation_id in self.store:
            return conversation_id

        new_id = str(uuid.uuid4())
        self.store[new_id] = []
        self.summaries[new_id] = ""
        return new_id

    def add_message(self, conversation_id :str , role :str, content: str):
        self.store[conversation_id].append({
            "role": role,
            "content": content
        })

    def get_messages(self, conversation_id: str) -> list:
        return self.store.get(conversation_id, [])

    def get_summary(self, conversation_id:str) -> str:
        return self.summaries.get(conversation_id, "")

    def update_summary(self, conversation_id: str, summary: str):
         self.summaries[conversation_id] = summary

    def should_summarize(self, conversation_id: str) -> bool:
        messages = self.get_messages(conversation_id)
        return len(messages) >= settings.SUMMARY_TRIGGER_MESSAGES

    def compress_conversation(self, conversation_id:str, summary: str):
        recent_messages = self.get_messages(conversation_id)[
            -settings.RECENT_MESSAGES_AFTER_SUMMARY:
        ]
        self.summaries[conversation_id] = summary
        self.store[conversation_id] = recent_messages

    def build_context_messages(self, conversation_id:str) -> List[dict]:
        messages: List[dict] = []

        summary = self.get_summary(conversation_id)
        if summary:
            messages.append({
                "role": "system",
                "content": f"Previous conversation summary: {summary}"
            })
        messages.extend(self.get_messages(conversation_id)[-settings.MAX_HISTORY_MESSAGES: ])
        return messages


    def get_recent_messages(self, conversation_id : str):
        messages = self.get_messages(conversation_id)
        return messages[-settings.MAX_HISTORY_MESSAGES: ]

memory_service = MemoryService()

