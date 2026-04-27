from typing import List

from openai import OpenAI

from app.core.config import settings

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def generate_reply(self, message: List[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "system",
                "content":" You are a helpful, friendly AI chatbot"
            },
            *message]

        )
        return response.choices[0].message.content

    def summarize_messages(self, messages: List[dict])-> str:
        responses = self.client.chat.completions.create(
            model=self.model,
            messages = [{
                "role": "system",
                "content": """
                Summarize this conversation for future context. 
                Preserve user preferences, goals, important facts, decisions, 
                and unresolved questions. Keep it concise."""
            },{
                "role": "user",
                "content": str(messages)
            }]
        )

        return responses.choices[0].message.content

llm_service = LLMService()