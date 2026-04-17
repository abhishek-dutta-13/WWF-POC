"""
LangSmith Tracer Module

Context managers for LangSmith tracing across all three AI features.
Each context manager sets the correct run name and passes session/course ID
as thread_id in metadata — all traces appear under project WWF-AI-Platform.

Usage:
    from langsmith_integration.tracer import chatbot_trace, mcq_trace, microlearning_trace, traceable

    # Chatbot — yields run_tree (use .id for run_id, .end(outputs=...) to set response)
    with chatbot_trace(session_id="abc-123", inputs={"query": "..."}) as run_tree:
        result = workflow.process_message(...)
        if run_tree:
            run_tree.end(outputs={"response": result["response"]})
    run_id = str(run_tree.id) if run_tree else None

    # MCQ Generation
    with mcq_trace(course_id="C001", inputs={"category": "..."}) as run_tree:
        mcq_set = process_category_mcqs(category)

    # Microlearning
    with microlearning_trace(course_id="C001", inputs={"category": "..."}) as run_tree:
        modules = generator.generate_microlearning_modules(...)

    # @traceable — creates a child span inside any active trace
    @traceable(run_type="llm", name="groq_response")
    def call_groq(messages):
        ...

Environment Variables Required:
    LANGCHAIN_API_KEY or LANGSMITH_API_KEY  — Your LangSmith API key
    LANGCHAIN_TRACING_V2 or LANGSMITH_TRACING — Set to "true" to enable tracing
    LANGSMITH_PROJECT                         — Project name (default: WWF-AI-Platform)
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional

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


def _noop_traceable(**kwargs):
    """No-op traceable decorator when langsmith is unavailable."""
    def decorator(fn):
        return fn
    return decorator


# Safe traceable decorator — creates child spans inside active traces.
# Falls back to a no-op if langsmith is not installed.
if _LANGSMITH_AVAILABLE:
    try:
        from langsmith import traceable
    except ImportError:
        traceable = _noop_traceable
else:
    traceable = _noop_traceable


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
def chatbot_trace(session_id: str, inputs: Optional[dict] = None):
    """
    LangSmith trace context for the AI Chatbot feature.

    Args:
        session_id: The chat session ID — used as thread_id in LangSmith metadata.
        inputs: Dict of inputs to record (e.g. {"query": "...", "language": "English"}).

    Yields:
        run_tree: The active LangSmith RunTree, or None if tracing is inactive.
        Use ``run_tree.end(outputs={...})`` before the with-block exits to record
        the response. Use ``str(run_tree.id)`` for the run_id.

    The trace appears in LangSmith as:
        Run name  : AI_Chatbot_Assistant
        Project   : WWF-AI-Platform
        Metadata  : {"thread_id": "<session_id>"}
    """
    if not _is_tracing_active():
        yield None
        return

    with _ls_trace(
        name="AI_Chatbot_Assistant",
        run_type="chain",
        project_name=_project_name(),
        metadata={"thread_id": session_id},
        inputs=inputs or {},
    ) as run_tree:
        yield run_tree


def submit_feedback(run_id: str, thumbs_up: bool) -> bool:
    """
    Submit human feedback (👍/👎) for a specific LangSmith trace run.

    Args:
        run_id:    The LangSmith run ID returned by chatbot_trace().
        thumbs_up: True = thumbs up (score=1, value="Good"),
                   False = thumbs down (score=0, value="Bad").

    Returns:
        True if feedback was submitted successfully, False otherwise.
    """
    if not _LANGSMITH_AVAILABLE:
        logger.warning("langsmith not installed — feedback submission skipped.")
        return False

    api_key = (
        os.getenv("LANGCHAIN_API_KEY", "") or
        os.getenv("LANGSMITH_API_KEY", "")
    )
    if not api_key:
        logger.warning("No LangSmith API key found — feedback submission skipped.")
        return False

    try:
        from langsmith import Client as _LSClient
        client = _LSClient(api_key=api_key)
        client.create_feedback(
            run_id=run_id,
            key="user_feedback",
            score=1 if thumbs_up else 0,
            value="Good" if thumbs_up else "Bad",
        )
        logger.info(f"Feedback submitted for run {run_id}: {'Good' if thumbs_up else 'Bad'}")
        return True
    except Exception as e:
        logger.error(f"Failed to submit feedback for run {run_id}: {e}")
        return False


@contextmanager
def mcq_trace(course_id: str, inputs: Optional[dict] = None):
    """
    LangSmith trace context for the MCQ Generation feature.

    Args:
        course_id: The course ID (e.g. "C001") — used as thread_id in LangSmith metadata.
        inputs: Dict of inputs to record (e.g. {"category": "Biodiversity"}).

    Yields:
        run_tree: The active LangSmith RunTree, or None if tracing is inactive.

    The trace appears in LangSmith as:
        Run name  : mcq_generation
        Project   : WWF-AI-Platform
        Metadata  : {"thread_id": "<course_id>"}
    """
    if not _is_tracing_active():
        yield None
        return

    with _ls_trace(
        name="mcq_generation",
        run_type="chain",
        project_name=_project_name(),
        metadata={"thread_id": course_id},
        inputs=inputs or {},
    ) as run_tree:
        yield run_tree


@contextmanager
def microlearning_trace(course_id: str, inputs: Optional[dict] = None):
    """
    LangSmith trace context for the Microlearning feature.

    Args:
        course_id: The course ID (e.g. "C001") — used as thread_id in LangSmith metadata.
        inputs: Dict of inputs to record (e.g. {"category": "Biodiversity", "language": "English"}).

    Yields:
        run_tree: The active LangSmith RunTree, or None if tracing is inactive.

    The trace appears in LangSmith as:
        Run name  : micro_learning
        Project   : WWF-AI-Platform
        Metadata  : {"thread_id": "<course_id>"}
    """
    if not _is_tracing_active():
        yield None
        return

    with _ls_trace(
        name="micro_learning",
        run_type="chain",
        project_name=_project_name(),
        metadata={"thread_id": course_id},
        inputs=inputs or {},
    ) as run_tree:
        yield run_tree
