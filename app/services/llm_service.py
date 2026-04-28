import json
from typing import List

from openai import OpenAI

from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
            max_retries=settings.OPENAI_MAX_RETRIES,

        )
        self.model = settings.OPENAI_MODEL

    def generate_reply(self, messages: List[dict], trace_id: str) -> str:
        try:
            logger.info(
                "llm_request_started",
                extra={
                    "trace_id": trace_id,
                    "event": "llm_request_started",
                    "model": self.model,
                },
            )

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

            logger.info(
                "llm_request_success",
                extra={
                    "trace_id": trace_id,
                    "event": "llm_request_success",
                    "model": self.model,
                },
            )

            return response.choices[0].message.content or ""

        except Exception:
            logger.exception(
                "llm_request_failed",
                extra={
                    "trace_id": trace_id,
                    "event": "llm_request_failed",
                    "model": self.model,
                },
            )
            raise

    def summarize_messages(self, messages: List[dict], trace_id: str) -> str:
        try:
            logger.info(
                "llm_summary_started",
                extra={
                    "trace_id": trace_id,
                    "event": "llm_summary_started",
                },
            )

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

            logger.info(
                "llm_summary_success",
                extra={
                    "trace_id": trace_id,
                    "event": "llm_summary_success",
                },
            )

            return response.choices[0].message.content or ""

        except Exception:
            logger.exception(
                "llm_summary_failed",
                extra={
                    "trace_id": trace_id,
                    "event": "llm_summary_failed",
                },
            )
            raise

    def extract_user_facts(self, message: str, trace_id: str) -> dict:
        try:
            logger.info(
                "llm_extract_started",
                extra={
                    "trace_id": trace_id,
                    "event": "llm_extract_started",
                },
            )

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
            result = json.loads(content)

            logger.info(
                "llm_extract_success",
                extra={
                    "trace_id": trace_id,
                    "event": "llm_extract_success",
                    "extracted_keys": list(result.keys()),
                },
            )

            return result

        except Exception:
            logger.exception(
                "llm_extract_failed",
                extra={
                    "trace_id": trace_id,
                    "event": "llm_extract_failed",
                },
            )
            return {}


llm_service = LLMService()