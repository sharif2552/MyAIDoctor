import os

from backend.utils.logging import get_logger


def configure_langsmith() -> None:
    logger = get_logger("myaidoc.tracing")
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() in {"1", "true", "yes"}
    api_key_present = bool(os.getenv("LANGSMITH_API_KEY"))
    project = os.getenv("LANGSMITH_PROJECT", "MyAIDoctor")

    if tracing_enabled and api_key_present:
        logger.info("LangSmith tracing enabled (project=%s)", project)
        return

    if tracing_enabled and not api_key_present:
        logger.warning("LangSmith tracing requested but LANGSMITH_API_KEY is missing")
        return

    logger.info("LangSmith tracing disabled")
