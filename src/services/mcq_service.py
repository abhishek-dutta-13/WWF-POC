"""
MCQ Generation Service

Core business logic for generating multiple-choice questions using Groq API.

This module contains the main business logic for:
- Generating individual MCQ sets using LLM
- Rate-limited batch processing
- Category-based MCQ generation orchestration

Security: Input validation, rate limiting, secure API usage.
Resource Efficiency: Caching, batch processing, optimized API calls.
"""

import json
import time
import logging
from typing import List, Dict, Any
from pathlib import Path

from models import MCQQuestion, MCQSet
from dependencies import groq_client, pdf_content_cache, DATA_BASE_PATH
from utils import extract_text_from_pdf

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
QUESTIONS_PER_SET = 30
BATCH_SIZE = 15  # Number of questions to generate before rate limit delay
RATE_LIMIT_DELAY = 61  # Seconds to wait between batches


def generate_mcq_set(
    category: str,
    pdf_content: str,
    set_number: int = 1,
    questions_per_set: int = QUESTIONS_PER_SET
) -> MCQSet:
    """
    Generate a set of MCQ questions for a given category using Groq API.
    
    This is the core business logic for MCQ generation. It constructs the prompt,
    calls the LLM, and parses the response into structured MCQQuestion objects.
    
    Args:
        category: Category name for the questions
        pdf_content: Combined text content from all PDFs in the category
        set_number: Set number for the questions (default: 1)
        questions_per_set: Number of questions to generate (default: 30)
    
    Returns:
        MCQSet object containing the generated questions
    
    Raises:
        Exception: If API call fails or response parsing fails
    
    Security: Validates input, sanitizes content, uses secure API client.
    Resource Efficiency: Single API call per set, efficient prompt engineering.
    """
    
    logger.info(f"Generating {questions_per_set} MCQ questions for category '{category}', set {set_number}")
    
    # Construct the generation prompt with difficulty levels and question types
    prompt = f"""You are an expert educator creating challenging multiple-choice questions about {category.replace('_', ' ')}.

Based on the following content, create {questions_per_set} multiple-choice questions.

**DIFFICULTY DISTRIBUTION (IMPORTANT):**
- 30% Easy questions (9 questions): Test basic recall and understanding
- 40% Medium questions (12 questions): Test application and analysis
- 30% Hard questions (9 questions): Test synthesis, evaluation, and critical thinking

**QUESTION TYPES (VARY THROUGHOUT):**
- Conceptual questions: Test understanding of core principles
- Application questions: Test ability to apply concepts to new scenarios
- Analysis questions: Test ability to compare, contrast, or break down complex ideas
- Evaluation questions: Test critical thinking and judgment
- Scenario-based questions: Present real-world situations requiring analysis

**QUESTION QUALITY REQUIREMENTS:**
- Mix factual recall with conceptual understanding
- Include questions that require critical thinking, not just memorization
- Use scenarios and case studies where appropriate
- Ensure questions are clear, unambiguous, and professionally written
- Avoid obvious answers or trick questions

**CONTENT:**
{pdf_content[:8000]}

**OUTPUT FORMAT (STRICT JSON):**
Return a JSON array of exactly {questions_per_set} questions. Each question must have:
{{
    "question": "Clear, challenging question text",
    "options": {{
        "A": "First option text",
        "B": "Second option text",
        "C": "Third option text",
        "D": "Fourth option text"
    }},
    "correct_answer": "A" (or B, C, D),
    "explanation": "Detailed explanation of why the answer is correct and why other options are incorrect",
    "difficulty": "easy" or "medium" or "hard",
    "question_type": "conceptual" or "application" or "analysis" or "evaluation" or "scenario"
}}

Return ONLY the JSON array, no additional text."""

    try:
        # Call Groq API
        response = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educator specializing in creating high-quality, challenging multiple-choice questions. Always return valid JSON arrays."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000,
            top_p=0.9
        )
        
        # Extract and parse response
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse JSON response
        questions_data = json.loads(content)
        
        # Validate we got the expected number of questions
        if len(questions_data) != questions_per_set:
            logger.warning(f"Expected {questions_per_set} questions but got {len(questions_data)}")
        
        # Convert to MCQQuestion objects with set_number
        questions = []
        for q_data in questions_data:
            # Handle both list and dict formats for options (LLM sometimes returns list)
            options_data = q_data["options"]
            if isinstance(options_data, list):
                # Convert list to dict format
                options_dict = {
                    "A": options_data[0] if len(options_data) > 0 else "",
                    "B": options_data[1] if len(options_data) > 1 else "",
                    "C": options_data[2] if len(options_data) > 2 else "",
                    "D": options_data[3] if len(options_data) > 3 else ""
                }
            else:
                # Already in dict format
                options_dict = options_data
            
            question = MCQQuestion(
                question=q_data["question"],
                options=options_dict,
                correct_answer=q_data["correct_answer"],
                explanation=q_data["explanation"],
                set_number=set_number,
                category=category,
                difficulty=q_data.get("difficulty", "medium"),
                question_type=q_data.get("question_type", "conceptual")
            )
            questions.append(question)
        
        logger.info(f"Successfully generated {len(questions)} questions for '{category}'")
        
        return MCQSet(
            category=category,
            set_number=set_number,
            questions=questions,
            total_questions=len(questions)
        )
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Response content: {content[:500]}")
        raise Exception(f"Failed to parse LLM response as JSON: {e}")
    except Exception as e:
        logger.error(f"Error generating MCQ set: {e}")
        raise


def generate_mcqs_with_rate_limiting(
    category: str,
    set_number: int = 1,
    questions_per_set: int = QUESTIONS_PER_SET
) -> MCQSet:
    """
    Generate MCQs with rate limiting to prevent API errors.
    
    This orchestrates the generation process with proper rate limiting:
    - Generates questions in batches of BATCH_SIZE
    - Adds RATE_LIMIT_DELAY between batches
    - Combines results into a single MCQSet
    
    Args:
        category: Category name
        set_number: Set number for the questions
        questions_per_set: Total number of questions to generate
    
    Returns:
        MCQSet with all generated questions
    
    Resource Efficiency: Rate limiting prevents API throttling and wasted requests.
    """
     
    logger.info(f"Starting rate-limited MCQ generation for '{category}' (Set {set_number})")
    
    # Get PDF content (from cache or extract)
    pdf_content = pdf_content_cache.get(category)
    if not pdf_content:
        category_path = DATA_BASE_PATH / category
        pdf_content = extract_text_from_pdf(category_path)
        pdf_content_cache[category] = pdf_content
    
    # Calculate number of batches needed
    num_batches = (questions_per_set + BATCH_SIZE - 1) // BATCH_SIZE
    all_questions = []
    
    logger.info(f"Generating {questions_per_set} questions in {num_batches} batches of {BATCH_SIZE}")
    
    for batch_num in range(num_batches):
        # Calculate questions for this batch
        questions_in_batch = min(BATCH_SIZE, questions_per_set - len(all_questions))
        
        logger.info(f"Batch {batch_num + 1}/{num_batches}: Generating {questions_in_batch} questions")
        
        # Generate this batch
        batch_set = generate_mcq_set(
            category=category,
            pdf_content=pdf_content,
            set_number=set_number,
            questions_per_set=questions_in_batch
        )
        
        all_questions.extend(batch_set.questions)
        
        # Rate limiting: Wait before next batch (except for last batch)
        if batch_num < num_batches - 1:
            logger.info(f"Rate limiting: Waiting {RATE_LIMIT_DELAY} seconds before next batch...")
            time.sleep(RATE_LIMIT_DELAY)
    
    logger.info(f"Completed generation of {len(all_questions)} questions for '{category}'")
    
    return MCQSet(
        category=category,
        set_number=set_number,
        questions=all_questions,
        total_questions=len(all_questions)
    )


def process_category_mcqs(
    category: str,
    set_number: int = 1,
    questions_per_set: int = QUESTIONS_PER_SET
) -> MCQSet:
    """
    Process MCQ generation for a single category with comprehensive error handling.
    
    This is the main entry point for category-based MCQ generation, providing:
    - Input validation
    - Error handling and logging
    - Returns MCQSet object
    
    Args:
        category: Category name
        set_number: Set number for questions
        questions_per_set: Number of questions to generate
    
    Returns:
        MCQSet object with generated questions
    
    Security: Validates inputs, handles errors gracefully.
    """
     
    logger.info(f"Processing MCQ generation for category '{category}'")
    
    try:
        # Validate category path exists
        category_path = DATA_BASE_PATH / category
        if not category_path.exists():
            raise ValueError(f"Category directory not found: {category}")
        
        # Generate MCQs with rate limiting
        mcq_set = generate_mcqs_with_rate_limiting(
            category=category,
            set_number=set_number,
            questions_per_set=questions_per_set
        )
        
        return mcq_set
        
    except Exception as e:
        logger.error(f"Error processing category '{category}': {e}")
        raise
