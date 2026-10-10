import json
import logging
from typing import Any


logger = logging.getLogger("panvel.observability")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

logger.propagate = False


def log_turn(
    *,
    trace_id: str,
    route: str,
    latency_ms: float,
    usage: dict[str, Any] | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    sources: list[str] | None = None,
    retrieved_documents: list[dict[str, Any]] | None = None,
) -> None:
    retrieved_documents_summary = [
        {
            "source": document.get("source"),
            "chunk_index": document.get("chunk_index"),
            "score": document.get("score"),
        }
        for document in (retrieved_documents or [])
    ]

    event = {
        "event": "chat_turn_completed",
        "trace_id": trace_id,
        "route": route,
        "latency_ms": latency_ms,
        "usage": usage,
        "tool_calls": tool_calls or [],
        "sources": sources or [],
        "retrieved_documents": retrieved_documents_summary,
    }

    logger.info(
        json.dumps(
            event,
            ensure_ascii=False,
        )
    )


def log_error(
    *,
    trace_id: str,
    latency_ms: float,
    error: Exception,
) -> None:
    event = {
        "event": "chat_turn_failed",
        "trace_id": trace_id,
        "latency_ms": latency_ms,
        "error_type": type(error).__name__,
        "error_message": str(error),
    }

    logger.error(
        json.dumps(
            event,
            ensure_ascii=False,
        )
    )