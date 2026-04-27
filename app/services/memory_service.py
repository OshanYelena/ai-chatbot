import uuid
from typing import Dict, List


class MemoryService:
    def __init__(self):
        self.store: Dict[str, List[dict]] = {}

    def get_or_create_conversation(self, conversation_id : str | None) -> str:
        if conversation_id and conversation_id in self.store:
            return conversation_id

        new_id = str(uuid.uuid4())
        self.store[new_id] = []
        return new_id

    def add_message(self, conversation_id :str , role :str, content: str):
        self.store[conversation_id].append({
            "role": role,
            "content": content
        })

    def get_messages(self, conversation_id: str) -> list:
        return self.store.get(conversation_id, [])

memory_service = MemoryService()

