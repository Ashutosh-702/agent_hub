import sys

import structlog
import orjson
import logging
from structlog import contextvars
from structlog.stdlib import BoundLogger, LoggerFactory
from datetime import datetime


def add_timestamp(_, __, event_dict):
    """Add current datetime to log event."""
    event_dict["timestamp"] = datetime.now().isoformat()
    return event_dict


def get_logger(*args, **kwargs) -> BoundLogger:
    """Create structlog logger for logging."""

    if not logging.getLogger().handlers:
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=logging.INFO,
            force=True,
        )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
            contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(
                serializer=lambda obj, **kw: orjson.dumps(
                    obj,
                    option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
                    default=str
                ).decode()
            )
        ],
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )
    return structlog.get_logger(**kwargs)


logger = get_logger() 