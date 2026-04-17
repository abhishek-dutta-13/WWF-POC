"""
LangSmith Integration Module

Provides tracing context managers for all three AI features:
- Chatbot (AI_Chatbot_Assistant)
- MCQ Generation (mcq_generation)
- Microlearning (micro_learning)

Project: WWF-AI-Platform
Thread ID: session_id / course_id passed via metadata
"""

from .tracer import chatbot_trace, mcq_trace, microlearning_trace, submit_feedback, traceable

__all__ = ["chatbot_trace", "mcq_trace", "microlearning_trace", "submit_feedback", "traceable"]
