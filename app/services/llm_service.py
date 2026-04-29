import json
import time
from typing import List

from openai import OpenAI
from opentelemetry import trace

from app.core.config import settings
from app.core.logger import setup_logger
from app.core.memory_config import STRUCTURED_MEMORY_KEYS, DYNAMIC_PREFIX

logger = setup_logger(__name__)
tracer = trace.get_tracer(__name__)


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
            max_retries=settings.OPENAI_MAX_RETRIES,
        )
        self.model = settings.OPENAI_MODEL

    def _log_success(self, trace_id: str, operation: str, start_time: float, usage=None, extra: dict | None = None):
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        log_extra = {
            "trace_id": trace_id,
            "event": "llm_request_success",
            "operation": operation,
            "model": self.model,
            "latency_ms": latency_ms,
            "prompt_tokens": usage.prompt_tokens if usage else None,
            "completion_tokens": usage.completion_tokens if usage else None,
            "total_tokens": usage.total_tokens if usage else None,
        }

        if extra:
            log_extra.update(extra)

        logger.info("llm_request_success", extra=log_extra)

    def _log_failure(self, trace_id: str, operation: str, start_time: float, error: Exception):
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        logger.exception(
            "llm_request_failed",
            extra={
                "trace_id": trace_id,
                "event": "llm_request_failed",
                "operation": operation,
                "model": self.model,
                "latency_ms": latency_ms,
                "error_message": str(error),
            },
        )

    def _log_started(self, trace_id: str, operation: str, input_messages_count: int):
        logger.info(
            "llm_request_started",
            extra={
                "trace_id": trace_id,
                "event": "llm_request_started",
                "operation": operation,
                "model": self.model,
                "input_messages_count": input_messages_count,
            },
        )

    def _set_usage_span_attributes(self, span, usage):
        if usage:
            span.set_attribute("llm.prompt_tokens", usage.prompt_tokens)
            span.set_attribute("llm.completion_tokens", usage.completion_tokens)
            span.set_attribute("llm.total_tokens", usage.total_tokens)

    def generate_reply(self, messages: List[dict], trace_id: str) -> str:
        operation = "generate_reply"
        start_time = time.perf_counter()

        with tracer.start_as_current_span("llm.generate_reply") as span:
            span.set_attribute("llm.operation", operation)
            span.set_attribute("llm.model", self.model)
            span.set_attribute("llm.input_messages_count", len(messages))

            try:
                self._log_started(trace_id, operation, len(messages))

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

                self._set_usage_span_attributes(span, response.usage)
                span.set_attribute("llm.status", "success")

                self._log_success(
                    trace_id=trace_id,
                    operation=operation,
                    start_time=start_time,
                    usage=response.usage,
                )

                return response.choices[0].message.content or ""

            except Exception as e:
                span.record_exception(e)
                span.set_attribute("llm.status", "failed")
                span.set_attribute("llm.error_message", str(e))
                self._log_failure(trace_id, operation, start_time, e)
                raise

    def summarize_messages(self, messages: List[dict], trace_id: str) -> str:
        operation = "summarize_messages"
        start_time = time.perf_counter()

        with tracer.start_as_current_span("llm.summarize_messages") as span:
            span.set_attribute("llm.operation", operation)
            span.set_attribute("llm.model", self.model)
            span.set_attribute("llm.input_messages_count", len(messages))

            try:
                self._log_started(trace_id, operation, len(messages))

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

                self._set_usage_span_attributes(span, response.usage)
                span.set_attribute("llm.status", "success")

                self._log_success(
                    trace_id=trace_id,
                    operation=operation,
                    start_time=start_time,
                    usage=response.usage,
                )

                return response.choices[0].message.content or ""

            except Exception as e:
                span.record_exception(e)
                span.set_attribute("llm.status", "failed")
                span.set_attribute("llm.error_message", str(e))
                self._log_failure(trace_id, operation, start_time, e)
                raise

    def extract_user_facts(self, message: str, trace_id: str) -> dict:
        operation = "extract_user_facts"
        start_time = time.perf_counter()

        with tracer.start_as_current_span("llm.extract_user_facts") as span:
            span.set_attribute("llm.operation", operation)
            span.set_attribute("llm.model", self.model)
            span.set_attribute("llm.input_messages_count", 1)

            try:
                self._log_started(trace_id, operation, 1)

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
                raw_facts = json.loads(content)

                structured = {}
                dynamic = {}

                for key, value in raw_facts.items():
                    normalized_key = key.lower().strip()

                    if normalized_key in STRUCTURED_MEMORY_KEYS:
                        structured[normalized_key] = value
                    else:
                        dynamic[f"{DYNAMIC_PREFIX}{normalized_key}"] = value

                final_memory = {**structured, **dynamic}

                self._set_usage_span_attributes(span, response.usage)
                span.set_attribute("llm.status", "success")
                span.set_attribute("llm.extracted_keys", ",".join(final_memory.keys()))
                span.set_attribute("llm.structured_keys", ",".join(structured.keys()))
                span.set_attribute("llm.dynamic_keys", ",".join(dynamic.keys()))

                self._log_success(
                    trace_id=trace_id,
                    operation=operation,
                    start_time=start_time,
                    usage=response.usage,
                    extra={
                        "structured_keys": list(structured.keys()),
                        "dynamic_keys": list(dynamic.keys()),
                        "extracted_keys": list(final_memory.keys()),
                    },
                )

                return final_memory

            except Exception as e:
                span.record_exception(e)
                span.set_attribute("llm.status", "failed")
                span.set_attribute("llm.error_message", str(e))
                self._log_failure(trace_id, operation, start_time, e)
                return {}

    def detect_memory_confirmation(self, message: str, trace_id: str) -> str:
        operation = "detect_memory_confirmation"
        start_time = time.perf_counter()

        with tracer.start_as_current_span("llm.detect_memory_confirmation") as span:
            span.set_attribute("llm.operation", operation)
            span.set_attribute("llm.model", self.model)
            span.set_attribute("llm.input_messages_count", 1)

            try:
                self._log_started(trace_id, operation, 1)

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Classify whether the user is confirming a memory update. "
                                "Return only one word: confirm, reject, or unclear."
                            ),
                        },
                        {
                            "role": "user",
                            "content": message,
                        },
                    ],
                    temperature=0,
                    max_tokens=10,
                )

                result = (response.choices[0].message.content or "unclear").strip().lower()

                if result not in {"confirm", "reject", "unclear"}:
                    result = "unclear"

                self._set_usage_span_attributes(span, response.usage)
                span.set_attribute("llm.status", "success")
                span.set_attribute("llm.classification", result)

                self._log_success(
                    trace_id=trace_id,
                    operation=operation,
                    start_time=start_time,
                    usage=response.usage,
                    extra={
                        "classification": result,
                    },
                )

                return result

            except Exception as e:
                span.record_exception(e)
                span.set_attribute("llm.status", "failed")
                span.set_attribute("llm.error_message", str(e))
                self._log_failure(trace_id, operation, start_time, e)
                return "unclear"


llm_service = LLMService()