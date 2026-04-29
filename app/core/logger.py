import logging
import json
import traceback
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

        for field in [

            "trace_id",

            "conversation_id",

            "user_id",

            "event",

            "model",

            "extracted_keys",
            "operation",

            "latency_ms",

            "input_messages_count",

            "prompt_tokens",

            "completion_tokens",

            "total_tokens",

            "error_message",

            "structured_keys",

            "dynamic_keys",

            "extracted_keys",

            "classification",

        ]:

            if hasattr(record, field):

                log_record[field] = getattr(record, field)

        if record.exc_info:

            log_record["exception"] = {

                "type": record.exc_info[0].__name__,

                "message": str(record.exc_info[1]),

                "traceback": traceback.format_exception(*record.exc_info),

            }

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