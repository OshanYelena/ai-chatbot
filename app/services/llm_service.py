import json
from typing import List

from openai import OpenAI

from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)


class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def generate_reply(self, messages: List[dict]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful, friendly AI chatbot.",
                    },
                    *messages,
                ],
                temperature=0.7,
                max_tokens=500,
            )

            return response.choices[0].message.content or ""

        except Exception:
            logger.exception("LLM reply generation failed")
            raise

    def summarize_messages(self, messages: List[dict]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Summarize this conversation for future context. "
                            "Preserve user preferences, goals, important facts, decisions, "
                            "and unresolved questions. Keep it concise."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(messages),
                    },
                ],
                temperature=0.2,
                max_tokens=300,
            )

            return response.choices[0].message.content or ""

        except Exception:
            logger.exception("Conversation summarization failed")
            raise

    def extract_user_facts(self, message: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract stable user facts from this message. "
                            "Only extract useful long-term information like name, preferences, goals. "
                            "Return valid JSON only. If nothing useful, return {}."
                        ),
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ],
                temperature=0,
                max_tokens=200,
            )

            content = response.choices[0].message.content or "{}"
            return json.loads(content)

        except Exception:
            logger.exception("User fact extraction failed")
            return {}


llm_service = LLMService()