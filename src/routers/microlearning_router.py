"""
Microlearning Router - Handles microlearning module generation

This router contains endpoints for RAG-based microlearning content generation.

Security: Implements API key authentication and input validation.
"""

import logging
from fastapi import APIRouter, HTTPException, Body, Depends

from models import MCQRequest
from dependencies import verify_api_key, get_microlearning_generator, COURSE_ID_TO_CATEGORY
from services.microlearning_generator import MicrolearningGenerator

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="",
    tags=["Microlearning"],
    dependencies=[]
)


@router.post("/generate-microlearning-quickbase")
async def generate_microlearning_quickbase(
    request: MCQRequest = Body(...),
    authenticated: bool = Depends(verify_api_key),
    generator: MicrolearningGenerator = Depends(get_microlearning_generator)
):
    """
    Generate comprehensive micro-learning modules for a course using RAG.
    
    This endpoint uses a RAG (Retrieval-Augmented Generation) approach:
    1. Retrieves relevant content from ChromaDB vector store
    2. Uses Groq LLM to generate structured micro-learning modules
    3. Returns detailed, extensive content (150-300 words per micro-content)
    
    **Request Body**:
    ```json
    {
        "CourseID": "001"
    }
    ```
    
    **Features**:
    - 4-6 chapters per category
    - 3-5 micro-contents per chapter
    - Each micro-content: 150-300 words
    - Comprehensive coverage of sustainability topics
    - Professional, accessible language
    
    **Technical Details**:
    - Uses ChromaDB vector store for content retrieval
    - Groq LLM (Meta Llama 4 Scout) for generation
    - Category-based metadata filtering
    - Retrieves top 20 most relevant chunks
    
    **Security**: Validates CourseID input, implements authentication if API_KEY is set.
    **Accessibility**: Returns structured JSON suitable for accessible UI rendering.
    **Resource Efficiency**: Uses RAG to avoid processing large PDFs on each request.
    """
    try:
        course_id = request.CourseID
        logger.info(f"Microlearning generation requested for CourseID: {course_id}")
        
        # Map CourseID to category
        category = COURSE_ID_TO_CATEGORY.get(course_id)
        if not category:
            logger.warning(f"Invalid CourseID requested: {course_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid CourseID. Allowed CourseIDs: {', '.join(COURSE_ID_TO_CATEGORY.keys())}"
            )
        
        logger.info(f"CourseID '{course_id}' mapped to category: {category}")
        
        # Generate micro-learning modules using RAG
        logger.info(f"Generating micro-learning modules for category: {category}")
        modules = generator.generate_microlearning_modules(
            category=category,
            top_k_chunks=20,
            max_chunks_for_llm=15
        )
        
        # Check for errors
        if 'error' in modules and not modules.get('chapters'):
            logger.error(f"Failed to generate modules: {modules.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate micro-learning modules: {modules.get('error')}"
            )
        
        # Update courseId in response to use the actual course_id
        modules['courseId'] = course_id
        
        # Add chapter IDs if not present
        for idx, chapter in enumerate(modules.get('chapters', []), start=1):
            if 'chapterId' not in chapter:
                chapter['chapterId'] = f"CH-{idx:03d}"
        
        # Validate quality
        validation = generator.validate_modules(modules)
        
        if not validation['valid']:
            logger.warning(f"Generated modules failed validation: {validation['errors']}")
        
        if validation['warnings']:
            logger.warning(f"Validation warnings: {validation['warnings']}")
        
        # Log statistics
        stats = validation.get('statistics', {})
        logger.info(
            f"Successfully generated {stats.get('chapter_count', 0)} chapters "
            f"with {stats.get('total_micro_contents', 0)} micro-contents for CourseID {course_id}"
        )
        
        return modules
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_microlearning_quickbase: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
