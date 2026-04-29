from typing import Dict, List


class PendingMemoryService:
    def __init__(self):
        self.pending_conflicts: Dict[str, List[dict]] = {}

    def set_pending_conflicts(self, conversation_id: str, conflicts: List[dict]):
        self.pending_conflicts[conversation_id] = conflicts

    def get_pending_conflicts(self, conversation_id: str) -> List[dict]:
        return self.pending_conflicts.get(conversation_id, [])

    def clear_pending_conflicts(self, conversation_id: str):
        self.pending_conflicts.pop(conversation_id, None)


pending_memory_service = PendingMemoryService()