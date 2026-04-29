from app.core.logger import setup_logger
from opentelemetry import trace

logger = setup_logger(__name__)
tracer = trace.get_tracer(__name__)


class EvalService:
    def evaluate_response(
        self,
        repo,
        reply: str,
        trace_id: str,
        user_id: str | None = None,
        conversation_id: str | None = None,
        operation: str = "generate_reply",
    ) -> dict:
        with tracer.start_as_current_span("eval.response_quality") as span:
            result = {
                "operation": operation,
                "passed": True,
                "issues": [],
                "reply_length": len(reply or ""),
            }

            if not reply or not reply.strip():
                result["passed"] = False
                result["issues"].append("empty_response")

            if len(reply or "") < 5:
                result["passed"] = False
                result["issues"].append("too_short")

            if len(reply or "") > 3000:
                result["passed"] = False
                result["issues"].append("too_long")

            repo.create_llm_eval_result(
                trace_id=trace_id,
                user_id=user_id,
                conversation_id=conversation_id,
                operation=operation,
                passed=result["passed"],
                issues=result["issues"],
                metadata={
                    "reply_length": result["reply_length"],
                },
            )

            span.set_attribute("eval.operation", operation)
            span.set_attribute("eval.passed", result["passed"])
            span.set_attribute("eval.issues", ",".join(result["issues"]))
            span.set_attribute("eval.reply_length", result["reply_length"])

            logger.info(
                "llm_eval_result",
                extra={
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "event": "llm_eval_result",
                    "operation": operation,
                    "eval_passed": result["passed"],
                    "eval_issues": result["issues"],
                    "reply_length": result["reply_length"],
                },
            )

            return result

    def evaluate_memory_extraction(
        self,
        repo,
        extracted_facts: dict,
        trace_id: str,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ) -> dict:
        operation = "extract_user_facts"

        with tracer.start_as_current_span("eval.memory_extraction") as span:
            result = {
                "operation": operation,
                "passed": True,
                "issues": [],
                "extracted_count": len(extracted_facts),
            }

            if len(extracted_facts) > 10:
                result["passed"] = False
                result["issues"].append("too_many_memory_keys")

            for key, value in extracted_facts.items():
                if not isinstance(key, str):
                    result["passed"] = False
                    result["issues"].append("invalid_key_type")

                if value is None or value == "":
                    result["passed"] = False
                    result["issues"].append(f"empty_value:{key}")

                if isinstance(value, (dict, list)):
                    result["issues"].append(f"nested_value:{key}")

            repo.create_llm_eval_result(
                trace_id=trace_id,
                user_id=user_id,
                conversation_id=conversation_id,
                operation=operation,
                passed=result["passed"],
                issues=result["issues"],
                metadata={
                    "extracted_count": result["extracted_count"],
                    "extracted_keys": list(extracted_facts.keys()),
                },
            )

            span.set_attribute("eval.operation", operation)
            span.set_attribute("eval.passed", result["passed"])
            span.set_attribute("eval.issues", ",".join(result["issues"]))
            span.set_attribute("eval.extracted_count", result["extracted_count"])
            span.set_attribute("eval.extracted_keys", ",".join(extracted_facts.keys()))

            logger.info(
                "memory_eval_result",
                extra={
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "event": "memory_eval_result",
                    "operation": operation,
                    "eval_passed": result["passed"],
                    "eval_issues": result["issues"],
                    "extracted_count": result["extracted_count"],
                },
            )

            return result

    def evaluate_confirmation_classification(
        self,
        repo,
        classification: str,
        trace_id: str,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ) -> dict:
        operation = "detect_memory_confirmation"

        with tracer.start_as_current_span("eval.confirmation_classification") as span:
            allowed = {"confirm", "reject", "unclear"}

            result = {
                "operation": operation,
                "passed": classification in allowed,
                "issues": [],
                "classification": classification,
            }

            if classification not in allowed:
                result["issues"].append("invalid_classification")

            repo.create_llm_eval_result(
                trace_id=trace_id,
                user_id=user_id,
                conversation_id=conversation_id,
                operation=operation,
                passed=result["passed"],
                issues=result["issues"],
                metadata={
                    "classification": result["classification"],
                },
            )

            span.set_attribute("eval.operation", operation)
            span.set_attribute("eval.passed", result["passed"])
            span.set_attribute("eval.issues", ",".join(result["issues"]))
            span.set_attribute("eval.classification", classification)

            logger.info(
                "classification_eval_result",
                extra={
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "event": "classification_eval_result",
                    "operation": operation,
                    "eval_passed": result["passed"],
                    "eval_issues": result["issues"],
                    "classification": classification,
                },
            )

            return result


eval_service = EvalService()