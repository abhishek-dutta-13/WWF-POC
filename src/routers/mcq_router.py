"""
MCQ Router - Handles all MCQ-related endpoints

This router contains endpoints for MCQ generation and Quickbase integration.

Security: Implements API key authentication and input validation.
Architecture: Uses services layer for business logic, utils for transformations.
"""

import os
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body, Depends

from models import MCQRequest, MCQResponse
from dependencies import verify_api_key, COURSE_ID_TO_CATEGORY, DATA_BASE_PATH
from services import process_category_mcqs  # Business logic
from utils import transform_to_quickbase_format  # Utility function
from quickbase_client import push_mcqs_to_quickbase

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="",
    tags=["MCQ Generation"],
    dependencies=[]
)


@router.post("/generate-mcqs", response_model=MCQResponse)
async def generate_mcqs(
    request: MCQRequest = Body(...),
    authenticated: bool = Depends(verify_api_key)
) -> MCQResponse:
    """
    Generate MCQ questions for a specified course.
    
    Generates 1 set of 30 MCQs with 4 options, correct answer, and explanation.
    
    **Rate Limiting**: 61-second delays every 15 questions (2 batches total).
    **Model**: Meta Llama 4 Scout 17B 16E Instruct.
    **Authentication**: Include X-API-Key header if API_KEY is configured.
    """
    try:
        course_id = request.CourseID
        logger.info(f"Received MCQ generation request for CourseID: {course_id}")
        
        category = COURSE_ID_TO_CATEGORY.get(course_id)
        if not category:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid CourseID. Must be one of: {list(COURSE_ID_TO_CATEGORY.keys())}"
            )
        
        logger.info(f"CourseID '{course_id}' mapped to category: {category}")
        
        mcq_set = process_category_mcqs(category)
        
        if not mcq_set:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate MCQs for CourseID: {course_id}"
            )
        
        response = MCQResponse(
            status="success",
            category=category,
            mcq_sets=[mcq_set],  # Wrap in list since MCQResponse expects a list
            total_sets=1,
            message=f"Successfully generated 1 MCQ set with {mcq_set.total_questions} questions for CourseID {course_id}"
        )
        
        logger.info(f"Successfully generated 1 set with {mcq_set.total_questions} questions for CourseID {course_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_mcqs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/generate-mcqs-quickbase")
async def generate_mcqs_quickbase(
    request: MCQRequest = Body(...),
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Generate MCQ questions and push them to Quickbase.
    
    Automatically generates MCQs, transforms to Quickbase format, and pushes to Quickbase.
    
    **Field mappings**:
    - 19: course_id
    - 8: set_number
    - 10: question_no
    - 18: question text
    - 11-14: options A-D
    - 15: correct_answer
    - 16: explanation
    
    **Environment Variables Required**:
    - QUICKBASE_TABLE_ID
    - QUICKBASE_USER_TOKEN
    - QUICKBASE_REALM_HOSTNAME
    """
    try:
        course_id = request.CourseID
        logger.info(f"Generate and push requested for CourseID: {course_id}")
        
        category = COURSE_ID_TO_CATEGORY.get(course_id)
        if not category:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid CourseID. Must be one of: {list(COURSE_ID_TO_CATEGORY.keys())}"
            )
        
        logger.info(f"CourseID '{course_id}' mapped to category: {category}")
        
        mcq_set = process_category_mcqs(category)
        
        if not mcq_set:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate MCQs for CourseID {course_id}"
            )
        
        standard_response = {
            "status": "success",
            "category": category,
            "mcq_sets": [mcq_set.dict()],  # Convert to dict and wrap in list
            "total_sets": 1
        }
        
        quickbase_data = transform_to_quickbase_format(standard_response, course_id)
        logger.info(f"Transformed {len(quickbase_data['data'])} Quickbase records for CourseID {course_id}")
        
        # Push to Quickbase
        table_id = os.getenv("QUICKBASE_TABLE_ID", "bvxbt7fyw")
        
        push_result = push_mcqs_to_quickbase(
            table_id=table_id,
            mcq_records=quickbase_data["data"]
        )
        
        if push_result["success"]:
            logger.info(f"Successfully pushed {push_result['records_pushed']} records to Quickbase")
            return {
                "status": "success",
                "message": f"Generated and pushed {push_result['records_pushed']} MCQ records to Quickbase",
                "course_id": course_id,
                "category": category,
                "records_pushed": push_result["records_pushed"],
                "quickbase_data": quickbase_data,
                "quickbase_response": push_result.get("response", {})
            }
        else:
            logger.error(f"Failed to push records to Quickbase: {push_result.get('error')}")
            raise HTTPException(
                status_code=500,
                detail=f"Generated MCQs but failed to push to Quickbase: {push_result.get('error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_mcqs_quickbase: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
def get_categories():
    """
    Get list of available categories.
    
    Returns list of available categories with PDF counts.
    """
    from dependencies import ALLOWED_CATEGORIES
    
    categories_info = []
    
    for category in ALLOWED_CATEGORIES:
        category_path = DATA_BASE_PATH / category
        pdf_count = len(list(category_path.glob("*.pdf"))) if category_path.exists() else 0
        
        categories_info.append({
            "name": category,
            "pdf_count": pdf_count,
            "available": pdf_count > 0
        })
    
    return {
        "categories": categories_info,
        "total_categories": len(ALLOWED_CATEGORIES)
    }


@router.post("/clear-cache")
def clear_cache():
    """
    Clear the PDF content cache.
    
    Resource Efficiency: Allows manual cache clearing to free memory.
    """
    from dependencies import pdf_content_cache
    
    cache_size = len(pdf_content_cache)
    pdf_content_cache.clear()
    
    logger.info(f"Cache cleared: {cache_size} entries removed")
    
    return {
        "status": "success",
        "message": f"Cache cleared: {cache_size} entries removed"
    }
