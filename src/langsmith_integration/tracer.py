"""
LangSmith Tracer Module

Context managers for LangSmith tracing across all three AI features.
Each context manager sets the correct run name and passes session/course ID
as thread_id in metadata — all traces appear under project WWF-AI-Platform.

Usage:
    from langsmith_integration.tracer import chatbot_trace, mcq_trace, microlearning_trace

    # Chatbot
    with chatbot_trace(session_id="abc-123"):
        result = workflow.process_message(...)

    # MCQ Generation
    with mcq_trace(course_id="C001"):
        mcq_set = process_category_mcqs(category)

    # Microlearning
    with microlearning_trace(course_id="C001"):
        modules = generator.generate_microlearning_modules(...)

Environment Variables Required:
    LANGCHAIN_API_KEY or LANGSMITH_API_KEY  — Your LangSmith API key
    LANGCHAIN_TRACING_V2 or LANGSMITH_TRACING — Set to "true" to enable tracing
    LANGSMITH_PROJECT                         — Project name (default: WWF-AI-Platform)
"""

import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Check if langsmith is installed (done once at import — package presence is static)
try:
    from langsmith import trace as _ls_trace
    _LANGSMITH_AVAILABLE = True
except ImportError:
    _LANGSMITH_AVAILABLE = False
    logger.warning(
        "langsmith package not installed. "
        "Install with: pip install langsmith. "
        "LangSmith tracing will be disabled."
    )


def _is_tracing_active() -> bool:
    """
    Returns True only when all tracing conditions are met.
    Reads env vars dynamically so load_dotenv() order does not matter.
    """
    if not _LANGSMITH_AVAILABLE:
        return False
    tracing = (
        os.getenv("LANGCHAIN_TRACING_V2", "") or
        os.getenv("LANGSMITH_TRACING", "")
    )
    api_key = (
        os.getenv("LANGCHAIN_API_KEY", "") or
        os.getenv("LANGSMITH_API_KEY", "")
    )
    return tracing.lower() == "true" and bool(api_key)


def _project_name() -> str:
    return os.getenv("LANGSMITH_PROJECT", "WWF-AI-Platform")


@contextmanager
def chatbot_trace(session_id: str):
    """
    LangSmith trace context for the AI Chatbot feature.

    Args:
        session_id: The chat session ID — used as thread_id in LangSmith metadata.

    The trace appears in LangSmith as:
        Run name  : AI_Chatbot_Assistant
        Project   : WWF-AI-Platform
        Metadata  : {"thread_id": "<session_id>"}
    """
    if not _is_tracing_active():
        yield
        return

    with _ls_trace(
        name="AI_Chatbot_Assistant",
        run_type="chain",
        project_name=_project_name(),
        metadata={"thread_id": session_id},
    ):
        yield


@contextmanager
def mcq_trace(course_id: str):
    """
    LangSmith trace context for the MCQ Generation feature.

    Args:
        course_id: The course ID (e.g. "C001") — used as thread_id in LangSmith metadata.

    The trace appears in LangSmith as:
        Run name  : mcq_generation
        Project   : WWF-AI-Platform
        Metadata  : {"thread_id": "<course_id>"}
    """
    if not _is_tracing_active():
        yield
        return

    with _ls_trace(
        name="mcq_generation",
        run_type="chain",
        project_name=_project_name(),
        metadata={"thread_id": course_id},
    ):
        yield


@contextmanager
def microlearning_trace(course_id: str):
    """
    LangSmith trace context for the Microlearning feature.

    Args:
        course_id: The course ID (e.g. "C001") — used as thread_id in LangSmith metadata.

    The trace appears in LangSmith as:
        Run name  : micro_learning
        Project   : WWF-AI-Platform
        Metadata  : {"thread_id": "<course_id>"}
    """
    if not _is_tracing_active():
        yield
        return

    with _ls_trace(
        name="micro_learning",
        run_type="chain",
        project_name=_project_name(),
        metadata={"thread_id": course_id},
    ):
        yield
