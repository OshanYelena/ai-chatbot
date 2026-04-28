import logging
import json
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "service": "ai-chatbot",
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "trace_id"):
            log_record["trace_id"] = record.trace_id

        if hasattr(record, "conversation_id"):
            log_record["conversation_id"] = record.conversation_id

        if hasattr(record, "event"):
            log_record["event"] = record.event

        return json.dumps(log_record)


def setup_logger(name: str):
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)

    return logger