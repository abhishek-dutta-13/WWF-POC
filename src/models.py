"""
Pydantic Models for API Request/Response

This module contains all data models used across the API.

Security: Uses Pydantic validation to prevent injection attacks.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator


# Import COURSE_ID_TO_CATEGORY from dependencies to avoid circular import
# This will be set after dependencies module loads
COURSE_ID_TO_CATEGORY = {}


class MCQRequest(BaseModel):
    """
    Request model for MCQ and Microlearning generation.
    
    Security: Uses Pydantic validation to prevent injection attacks.
    """
    CourseID: str = Field(
        ...,
        description="Course ID (001, 002, 003)",
        example="001"
    )
    
    @validator('CourseID')
    def validate_course_id(cls, v):
        """Validate CourseID against whitelist to prevent injection."""
        if not COURSE_ID_TO_CATEGORY:
            # Mappings not loaded yet - will be validated later
            return v
        if v not in COURSE_ID_TO_CATEGORY:
            raise ValueError(f"CourseID must be one of: {list(COURSE_ID_TO_CATEGORY.keys())}")
        return v


class MCQOption(BaseModel):
    """Model for MCQ options."""
    A: str
    B: str
    C: str
    D: str


class MCQQuestion(BaseModel):
    """Model for a single MCQ question."""
    question: str
    options: MCQOption
    correct_answer: str = Field(..., pattern='^[A-D]$')
    explanation: str
    set_number: int = 1
    category: str = ""
    difficulty: str = "medium"
    question_type: str = "conceptual"


class MCQSet(BaseModel):
    """Model for a set of MCQ questions."""
    category: str
    set_number: int
    questions: List[MCQQuestion]
    total_questions: int


class MCQResponse(BaseModel):
    """Response model for MCQ generation."""
    status: str
    category: str
    mcq_sets: List[MCQSet]
    total_sets: int
    message: Optional[str] = None
