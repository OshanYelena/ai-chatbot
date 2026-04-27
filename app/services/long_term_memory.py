from typing import Dict

class LongTermMemoryService:
    def __init__(self):
        self.store: Dict[str, Dict[str, str]] = {}

    def get_memory(self, conversation_id: str) -> Dict[str, str]:
        return self.store.get(conversation_id, {})

    def update_memory(self, conversation_id:str, key: str, value:str):
        if conversation_id not in self.store:
            self.store[conversation_id] = {}

        self.store[conversation_id][key] = value

    def format_memory_for_prompt(self, conversation_id:str) ->str :
        memory = self.get_memory(conversation_id)

        if not memory:
            return ""
        formatted = "\n".join([f"{k}: {v}" for k, v in memory.items()])

        return f"User known facts:\n{formatted}"

long_term_memory_service = LongTermMemoryService()