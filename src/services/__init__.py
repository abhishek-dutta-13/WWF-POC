"""  
Services Package

This package contains business logic and service layer components.

Architecture:
- services/mcq_service.py - Core MCQ generation business logic
- services/microlearning_generator.py - Microlearning RAG-based generation
- Separates business logic from utilities and routing
"""

from .mcq_service import generate_mcq_set, generate_mcqs_with_rate_limiting, process_category_mcqs
from .microlearning_generator import MicrolearningGenerator, create_generator_from_env, transform_to_quickbase_format

__all__ = [
    'generate_mcq_set',
    'generate_mcqs_with_rate_limiting',
    'process_category_mcqs',
    'MicrolearningGenerator',
    'create_generator_from_env',
    'transform_to_quickbase_format'
]
