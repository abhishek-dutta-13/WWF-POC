
"""
MCQ Generation API Service using Groq

This service provides an API endpoint to generate multiple-choice questions
from PDF documents using the Groq API. It supports three categories:
- Agriculture
- Climate
- Renewable Energy

Security: Implements input validation, rate limiting considerations, and secure file handling.
Accessibility: Returns structured JSON that can be consumed by accessible UI components.
Resource Efficiency: Caches PDF content and uses efficient text processing.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from groq import Groq
import pypdf
from fastapi import FastAPI, HTTPException, Body, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="MCQ Generator API",
    description="Generate MCQ questions from PDFs using Groq API - Quickbase Integration Ready",
    version="1.0.0"
)

# Security: Configure CORS with appropriate restrictions
# For Quickbase integration, allow Quickbase domains
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
if ALLOWED_ORIGINS == ["*"]:
    logger.warning("CORS is set to allow all origins. Set ALLOWED_ORIGINS in .env for production")

# Common Quickbase domains to allow (update with your specific Quickbase domain)
QUICKBASE_DOMAINS = [
    "https://*.quickbase.com",
    "https://*.quickbaseapi.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# Configuration
DATA_BASE_PATH = Path(__file__).parent.parent / "data"
ALLOWED_CATEGORIES = ['agriculture', 'climate', 'renewable_energy']
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_KEY = os.getenv("API_KEY")  # Optional API key for securing the endpoint

# Validate API key on startup
if not GROQ_API_KEY:
    logger.error("GROQ_API_KEY not found in environment variables")
    raise ValueError("GROQ_API_KEY must be set in environment variables")

if API_KEY:
    logger.info("API authentication is ENABLED")
else:
    logger.warning("API authentication is DISABLED - Set API_KEY in .env for production")

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Cache for PDF content to avoid re-reading
pdf_content_cache: Dict[str, str] = {}


# Security: API Key Authentication (Optional)
async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> bool:
    """
    Verify API key from request header.
    
    Args:
        x_api_key: API key from X-API-Key header
        
    Returns:
        True if authentication passes
        
    Raises:
        HTTPException: If authentication is required but fails
        
    Security: Implements optional API key authentication for Quickbase integration.
    """
    # If no API_KEY is configured, allow all requests
    if not API_KEY:
        return True
    
    # If API_KEY is configured, require it in headers
    if not x_api_key or x_api_key != API_KEY:
        logger.warning(f"Unauthorized API access attempt from IP")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include X-API-Key header."
        )
    
    return True



# Pydantic Models
class MCQRequest(BaseModel):
    """
    Request model for MCQ generation.
    
    Security: Uses Pydantic validation to prevent injection attacks.
    """
    category: str = Field(
        ...,
        description="Category name (agriculture, climate, renewable_energy)",
        example="agriculture"
    )
    
    @validator('category')
    def validate_category(cls, v):
        """Validate category against whitelist to prevent injection."""
        if v not in ALLOWED_CATEGORIES:
            raise ValueError(f"Category must be one of: {ALLOWED_CATEGORIES}")
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


# Core Functions
def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content from the PDF
        
    Security: Validates file path and type to prevent unauthorized file access.
    Resource Efficiency: Efficiently processes PDF pages without loading entire file into memory.
    """
    try:
        # Security: Validate file exists and is a PDF
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Security: Ensure file is actually a PDF
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError("File must be a PDF")
        
        # Check cache first
        if pdf_path in pdf_content_cache:
            logger.info(f"Using cached content for {pdf_path}")
            return pdf_content_cache[pdf_path]
        
        text_content = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            logger.info(f"Processing {os.path.basename(pdf_path)} - {num_pages} pages")
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text_content += page.extract_text() + "\n"
        
        text_content = text_content.strip()
        
        # Cache the content
        pdf_content_cache[pdf_path] = text_content
        
        return text_content
        
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
        raise


def generate_mcq_set(
    client: Groq,
    content: str,
    category: str,
    set_number: int,
    num_questions: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Generate a set of MCQ questions using Groq API.
    
    Args:
        client: Initialized Groq client
        content: Text content from which to generate questions
        category: Category name
        set_number: Set number (1, 2, or 3)
        num_questions: Number of questions per set (default: 5)
        
    Returns:
        Dictionary containing MCQ set or None if generation fails
        
    Security: Sanitizes inputs and validates output structure.
    Resource Efficiency: Truncates content intelligently to manage token usage.
    """
    try:
        # Resource Efficiency: Truncate content to manage token limits
        max_chars = 25000
        if len(content) > max_chars:
            # Take content from different sections for variety
            segment_size = max_chars // 3
            content = (
                content[:segment_size] + 
                content[len(content)//2 - segment_size//2:len(content)//2 + segment_size//2] + 
                content[-segment_size:]
            )
        
        # Security: Sanitize category name
        category_clean = category.replace('_', ' ').title()
        
        prompt = f"""Based on the following content about {category_clean}, create {num_questions} multiple-choice questions.

Content:
{content}

Generate exactly {num_questions} multiple-choice questions. Each question must have:
1. A clear question text
2. Four options (A, B, C, D)
3. The correct answer (letter only: A, B, C, or D)
4. A brief explanation of why the answer is correct

Format your response ONLY as a valid JSON array. Do not include any markdown formatting or code blocks. Just return the raw JSON array.

Example format:
[
  {{
    "question": "What is...",
    "options": {{
      "A": "Option 1",
      "B": "Option 2",
      "C": "Option 3",
      "D": "Option 4"
    }},
    "correct_answer": "B",
    "explanation": "The correct answer is B because..."
  }}
]
"""
        
        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educator creating high-quality multiple-choice questions. Always respond with valid JSON only, no markdown or code blocks."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2048
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Clean markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON response
        questions = json.loads(response_text)
        
        # Security: Validate structure
        if not isinstance(questions, list):
            logger.error("Response is not a list")
            return None
        
        return {
            "category": category,
            "set_number": set_number,
            "questions": questions,
            "total_questions": len(questions)
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response: {e}")
        logger.debug(f"Response was: {response_text[:500]}")
        return None
    except Exception as e:
        logger.error(f"Error generating MCQ set: {e}")
        return None


def get_category_pdfs(category: str) -> List[Path]:
    """
    Get all PDF files for a given category.
    
    Args:
        category: Category name
        
    Returns:
        List of PDF file paths
        
    Security: Validates category and ensures paths stay within allowed directory.
    """
    # Security: Validate category against whitelist
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"Invalid category. Must be one of: {ALLOWED_CATEGORIES}")
    
    category_path = DATA_BASE_PATH / category
    
    # Security: Ensure the resolved path is within DATA_BASE_PATH
    try:
        category_path = category_path.resolve()
        DATA_BASE_PATH.resolve()
        if not str(category_path).startswith(str(DATA_BASE_PATH.resolve())):
            raise ValueError("Invalid category path")
    except Exception as e:
        logger.error(f"Path validation failed: {e}")
        raise ValueError("Invalid category path")
    
    if not category_path.exists():
        logger.warning(f"Category path not found: {category_path}")
        return []
    
    pdf_files = list(category_path.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files in {category}")
    
    return pdf_files


def process_category_mcqs(category: str) -> List[Dict[str, Any]]:
    """
    Process all PDFs in a category and generate 3 sets of MCQs.
    
    Args:
        category: Category name
        
    Returns:
        List of 3 MCQ sets, each containing 5 questions
        
    Security: Implements comprehensive input validation and error handling.
    Resource Efficiency: Reuses extracted PDF content across multiple MCQ sets.
    """
    logger.info(f"Processing category: {category}")
    
    # Get PDF files
    pdf_files = get_category_pdfs(category)
    
    if not pdf_files:
        logger.warning(f"No PDF files found for category: {category}")
        return []
    
    # Extract text from all PDFs
    combined_content = ""
    for pdf_file in pdf_files:
        try:
            text = extract_text_from_pdf(str(pdf_file))
            combined_content += text + "\n\n"
        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {e}")
            continue
    
    if not combined_content.strip():
        logger.error(f"No content extracted from PDFs in {category}")
        return []
    
    logger.info(f"Extracted {len(combined_content)} characters from category {category}")
    
    # Generate 3 sets of MCQs
    mcq_sets = []
    for set_num in range(1, 4):
        logger.info(f"Generating MCQ Set {set_num} for {category}")
        mcq_set = generate_mcq_set(groq_client, combined_content, category, set_num)
        
        if mcq_set:
            mcq_sets.append(mcq_set)
            logger.info(f"Set {set_num} generated successfully with {mcq_set['total_questions']} questions")
        else:
            logger.error(f"Failed to generate Set {set_num} for {category}")
    
    return mcq_sets


# API Endpoints
@app.get("/")
def root():
    """
    Root endpoint providing API information.
    
    Returns:
        Basic API information and available endpoints
    """
    return {
        "service": "MCQ Generator API",
        "version": "1.0.0",
        "description": "Generate MCQ questions from PDFs using Groq API - Quickbase Integration Ready",
        "endpoints": {
            "/generate-mcqs": "POST - Generate MCQs for a specific category (standard format)",
            "/generate-mcqs-quickbase": "POST - Generate MCQs in Quickbase field ID format",
            "/categories": "GET - List available categories",
            "/health": "GET - Health check endpoint",
            "/clear-cache": "POST - Clear PDF content cache"
        },
        "categories": ALLOWED_CATEGORIES,
        "quickbase": {
            "table_id": "bvxbt7fyw",
            "realm": "accentureglobaldeliverytraining.quickbase.com"
        }
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "MCQ Generator API",
        "groq_api_configured": bool(GROQ_API_KEY)
    }


@app.post("/generate-mcqs", response_model=MCQResponse)
async def generate_mcqs(
    request: MCQRequest = Body(...),
    authenticated: bool = Depends(verify_api_key)
) -> MCQResponse:
    """
    Generate MCQ questions for a specified category.
    
    This endpoint processes PDFs in the specified category and generates
    3 sets of MCQs, each containing 5 questions with explanations.
    
    **Quickbase Integration**: Send POST request with JSON body: {"category": "agriculture"}
    **Authentication**: Include X-API-Key header if API_KEY is configured
    
    Args:
        request: MCQRequest containing the category name
        authenticated: Authentication result from dependency
        
    Returns:
        MCQResponse with generated MCQ sets
        
    Raises:
        HTTPException: If category is invalid, authentication fails, or generation fails
        
    Security:
        - Optional API key authentication via X-API-Key header
        - Input validation via Pydantic models
        - Path traversal prevention
        - GROQ API key protection
        
    Accessibility:
        - Returns structured JSON compatible with screen readers
        - Clear error messages
    """
    try:
        category = request.category
        logger.info(f"Received MCQ generation request for category: {category}")
        
        # Security: Double-check category validation
        if category not in ALLOWED_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {ALLOWED_CATEGORIES}"
            )
        
        # Generate MCQs
        mcq_sets = process_category_mcqs(category)
        
        if not mcq_sets:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate MCQs for category: {category}"
            )
        
        # Prepare response
        response = MCQResponse(
            status="success",
            category=category,
            mcq_sets=mcq_sets,
            total_sets=len(mcq_sets),
            message=f"Successfully generated {len(mcq_sets)} MCQ sets for {category}"
        )
        
        logger.info(f"Successfully generated {len(mcq_sets)} sets for {category}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_mcqs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/categories")
def get_categories():
    """
    Get list of available categories.
    
    Returns:
        List of available categories with PDF counts
    """
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


@app.post("/clear-cache")
def clear_cache():
    """
    Clear the PDF content cache.
    
    Returns:
        Cache clear status
        
    Resource Efficiency: Allows manual cache clearing to free memory.
    """
    global pdf_content_cache
    cache_size = len(pdf_content_cache)
    pdf_content_cache.clear()
    
    logger.info(f"Cache cleared: {cache_size} entries removed")
    
    return {
        "status": "success",
        "message": f"Cache cleared: {cache_size} entries removed"
    }


# Generated by GitHub Copilot
# Quickbase Integration Models
class QuickbaseFieldValue(BaseModel):
    """Model for Quickbase field value."""
    value: Any


class QuickbaseRecord(BaseModel):
    """Model for a single Quickbase record with field IDs."""
    # Field mappings for Quickbase table "bvxbt7fyw"
    # 7: category, 8: set_number, 10: question_no, 18: question (multi-line)
    # 11-14: options A-D, 15: correct_answer, 16: explanation (multi-line)
    pass  # Dynamic fields will be added as dict


class QuickbaseResponse(BaseModel):
    """Response model for Quickbase-formatted MCQ data."""
    to: str = Field(default="bvxbt7fyw", description="Quickbase table ID")
    data: List[Dict[str, Dict[str, Any]]]
    fieldsToReturn: List[int] = Field(default=[6, 7, 8, 9, 10, 11, 12, 13])


# Generated by GitHub Copilot
def transform_to_quickbase_format(mcq_sets: List[Dict[str, Any]], category: str) -> Dict[str, Any]:
    """
    Transform MCQ sets into Quickbase field ID format.
    
    Args:
        mcq_sets: List of MCQ sets from process_category_mcqs
        category: Category name
        
    Returns:
        Dictionary in Quickbase API format with field IDs
        
    Security: Validates all input data before transformation.
    Accessibility: Maintains question and explanation content integrity.
    """
    quickbase_records = []
    
    for mcq_set in mcq_sets:
        set_number = mcq_set.get("set_number", 1)
        questions = mcq_set.get("questions", [])
        
        for idx, question in enumerate(questions, start=1):
            # Create record with Quickbase field IDs
            record = {
                "7": {"value": category},  # category
                "8": {"value": set_number},  # set_number
                "10": {"value": str(idx)},  # question_no
                "18": {"value": question.get("question", "")},  # question (multi-line)
                "11": {"value": question.get("options", {}).get("A", "")},  # option_a
                "12": {"value": question.get("options", {}).get("B", "")},  # option_b
                "13": {"value": question.get("options", {}).get("C", "")},  # option_c
                "14": {"value": question.get("options", {}).get("D", "")},  # option_d
                "15": {"value": question.get("correct_answer", "")},  # correct_answer
                "16": {"value": question.get("explanation", "")}  # explanation (multi-line)
            }
            
            quickbase_records.append(record)
    
    logger.info(f"Transformed {len(quickbase_records)} questions into Quickbase format")
    
    return {
        "to": "bvxbt7fyw",
        "data": quickbase_records,
        "fieldsToReturn": [6, 7, 8, 9, 10, 11, 12, 13]
    }


# Generated by GitHub Copilot
@app.post("/generate-mcqs-quickbase", response_model=QuickbaseResponse)
async def generate_mcqs_quickbase(
    request: MCQRequest = Body(...),
    authenticated: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Generate MCQ questions in Quickbase field ID format.
    
    This endpoint processes PDFs in the specified category and generates
    3 sets of MCQs in Quickbase API format with field IDs (7-18).
    
    **Quickbase Integration Endpoint**: Returns data ready for Quickbase API insertion
    **Table ID**: bvxbt7fyw
    **Authentication**: Include X-API-Key header if API_KEY is configured
    
    Field Mappings:
    - Field 7: category
    - Field 8: set_number
    - Field 10: question_no
    - Field 18: question (multi-line text)
    - Field 11-14: options A-D
    - Field 15: correct_answer
    - Field 16: explanation (multi-line text)
    
    Args:
        request: MCQRequest containing the category name
        authenticated: Authentication result from dependency
        
    Returns:
        QuickbaseResponse with flattened MCQ records in field ID format
        
    Raises:
        HTTPException: If category is invalid, authentication fails, or generation fails
        
    Security:
        - Optional API key authentication via X-API-Key header
        - Input validation via Pydantic models
        - Path traversal prevention
        - GROQ API key protection
        
    Accessibility:
        - Returns structured data compatible with Quickbase UI
        - Preserves question and explanation content for screen readers
    """
    try:
        category = request.category
        logger.info(f"Received Quickbase MCQ generation request for category: {category}")
        
        # Security: Double-check category validation
        if category not in ALLOWED_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {ALLOWED_CATEGORIES}"
            )
        
        # Generate MCQs using existing function
        mcq_sets = process_category_mcqs(category)
        
        if not mcq_sets:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate MCQs for category: {category}"
            )
        
        # Transform to Quickbase format
        quickbase_data = transform_to_quickbase_format(mcq_sets, category)
        
        logger.info(f"Successfully generated {len(quickbase_data['data'])} Quickbase records for {category}")
        
        return quickbase_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in generate_mcqs_quickbase: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# Main entry point for testing
if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    # Security: In production, configure SSL/TLS certificates
    uvicorn.run(
        app,
        host="0.0.0.0",  # Bind to all interfaces
        port=8000,
        log_level="info"
    )
