from app.core.logger import setup_logger

logger = setup_logger(__name__)


class EvalService:
    def evaluate_response(
        self,
        reply: str,
        trace_id: str,
        operation: str = "generate_reply",
    ) -> dict:
        result = {
            "operation": operation,
            "passed": True,
            "issues": [],
            "reply_length": len(reply or ""),
        }

        if not reply or not reply.strip():
            result["passed"] = False
            result["issues"].append("empty_response")

        if len(reply) < 5:
            result["passed"] = False
            result["issues"].append("too_short")

        if len(reply) > 3000:
            result["passed"] = False
            result["issues"].append("too_long")

        logger.info(
            "llm_eval_result",
            extra={
                "trace_id": trace_id,
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
        extracted_facts: dict,
        trace_id: str,
    ) -> dict:
        result = {
            "operation": "extract_user_facts",
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

        logger.info(
            "memory_eval_result",
            extra={
                "trace_id": trace_id,
                "event": "memory_eval_result",
                "operation": "extract_user_facts",
                "eval_passed": result["passed"],
                "eval_issues": result["issues"],
                "extracted_count": result["extracted_count"],
            },
        )

        return result

    def evaluate_confirmation_classification(
        self,
        classification: str,
        trace_id: str,
    ) -> dict:
        allowed = {"confirm", "reject", "unclear"}

        result = {
            "operation": "detect_memory_confirmation",
            "passed": classification in allowed,
            "issues": [],
            "classification": classification,
        }

        if classification not in allowed:
            result["issues"].append("invalid_classification")

        logger.info(
            "classification_eval_result",
            extra={
                "trace_id": trace_id,
                "event": "classification_eval_result",
                "operation": "detect_memory_confirmation",
                "eval_passed": result["passed"],
                "eval_issues": result["issues"],
                "classification": classification,
            },
        )

        return result


eval_service = EvalService()