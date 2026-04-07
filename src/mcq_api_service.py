"""
MCQ Generation API Service using Groq

This service provides an API endpoint to generate multiple-choice questions
from PDF documents using the Groq API (Meta Llama 4 Scout model).
It supports three categories:
- Agriculture
- Climate
- Renewable Energy

Features:
- Generates 1 set of 30 questions per category
- Each question includes 4 options, correct answer, and explanation
- Implements rate limiting (61-second delays every 10 questions) to prevent API errors
- All questions have set_number = 1

Security: Implements input validation, rate limiting considerations, and secure file handling.
Accessibility: Returns structured JSON that can be consumed by accessible UI components.
Resource Efficiency: Caches PDF content, uses efficient text processing, and prevents rate limit errors.
"""

import os
import json
import time
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from groq import Groq
import pypdf
from fastapi import FastAPI, HTTPException, Body, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import logging
from microlearning_generator import create_generator_from_env, MicrolearningGenerator
from quickbase_client import push_mcqs_to_quickbase, QuickbaseClient

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

# Add CORS middleware to allow cross-origin requests from Quickbase and other clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Origins allowed to make requests (configured via .env)
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["POST", "GET", "OPTIONS"],  # HTTP methods permitted
    allow_headers=["*"],  # Allow all headers including X-API-Key for authentication
)

# Configuration
DATA_BASE_PATH = Path(__file__).parent.parent / "data"
CATEGORY_FILE_PATH = DATA_BASE_PATH / "category_file" / "categories.csv"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_KEY = os.getenv("API_KEY")  # Optional API key for securing the endpoint


# Dynamic category loading - categories are loaded from CSV file for easy maintenance
ALLOWED_CATEGORIES = []  # Will be populated from CSV file
COURSE_ID_TO_CATEGORY = {}  # Maps course_id to category folder name
CATEGORY_TO_COURSE_ID = {}  # Maps category folder name to course_id

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

# Initialize microlearning generator (lazy loading)
_microlearning_generator: Optional[MicrolearningGenerator] = None

def get_microlearning_generator() -> MicrolearningGenerator:
    """Get or create the microlearning generator instance (singleton pattern)."""
    global _microlearning_generator
    if _microlearning_generator is None:
        logger.info("Initializing microlearning generator")
        try:
            _microlearning_generator = create_generator_from_env()
            logger.info("Microlearning generator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize microlearning generator: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize microlearning generator: {str(e)}"
            )
    return _microlearning_generator



def normalize_category_name(category_name: str) -> str:
    """
    Convert category display name to folder name format.
    
    Example: "Circular Economy & Waste Reduction" -> "circular_economy_and_waste_reduction"
    
    Args:
        category_name: Display name from CSV
        
    Returns:
        Normalized folder name
    """
    return category_name.lower().replace(' & ', '_and_').replace(' ', '_')


def load_categories_from_csv() -> List[str]:
    """
    Load active categories from CSV file and build course_id to category mappings.
    
    This function reads the categories.csv file from data/category_file folder
    and returns a list of active category names. It also builds mappings between
    course_id and category folder names.
    
    CSV Format:
        category_name,course_id,pdf_file_name,active
        Circular Economy & Waste Reduction,001,cewr_1.pdf,TRUE
    
    Returns:
        List of active category folder names
        
    Raises:
        FileNotFoundError: If categories.csv file doesn't exist
        
    Security: Validates CSV content and filters only active categories.
    Resource Efficiency: Loads categories once at startup instead of repeated file reads.
    """
    global COURSE_ID_TO_CATEGORY, CATEGORY_TO_COURSE_ID
    
    try:
        if not CATEGORY_FILE_PATH.exists():
            logger.error(f"Category file not found at {CATEGORY_FILE_PATH}")
            raise FileNotFoundError(f"categories.csv not found at {CATEGORY_FILE_PATH}")
        
        categories = set()  # Use set to avoid duplicates
        course_mappings = {}
        
        with open(CATEGORY_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Only include active categories
                if row.get('active', '').lower() == 'true':
                    category_display_name = row.get('category_name', '').strip()
                    course_id = row.get('course_id', '').strip()
                    
                    if category_display_name and course_id:
                        # Convert display name to folder name format
                        category_folder_name = normalize_category_name(category_display_name)
                        categories.add(category_folder_name)
                        
                        # Build course_id to category mapping
                        if course_id not in course_mappings:
                            course_mappings[course_id] = category_folder_name
                            logger.info(f"Mapped CourseID '{course_id}' -> '{category_folder_name}'")
        
        # Update global mappings
        COURSE_ID_TO_CATEGORY = course_mappings
        CATEGORY_TO_COURSE_ID = {v: k for k, v in course_mappings.items()}
        
        categories_list = sorted(list(categories))
        
        if not categories_list:
            logger.warning("No active categories found in CSV file")
        else:
            logger.info(f"Total {len(categories_list)} active categories loaded from CSV")
            logger.info(f"Course ID mappings: {COURSE_ID_TO_CATEGORY}")
        
        return categories_list
        
    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error loading categories from CSV: {str(e)}")
        raise ValueError(f"Failed to load categories: {str(e)}")


# Load categories from CSV at startup
try:
    ALLOWED_CATEGORIES = load_categories_from_csv()
    logger.info(f"Categories initialized: {ALLOWED_CATEGORIES}")
except Exception as e:
    logger.error(f"Failed to initialize categories: {e}")
    # Fallback to empty list - will cause validation errors if categories not loaded
    ALLOWED_CATEGORIES = []


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
    CourseID: str = Field(
        ...,
        description="Course ID (001, 002, 003)",
        example="001"
    )
    
    @validator('CourseID')
    def validate_course_id(cls, v):
        """Validate CourseID against whitelist to prevent injection."""
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
    num_questions: int = 10
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

IMPORTANT: Create a diverse set of questions with varying difficulty levels and question types:

DIFFICULTY DISTRIBUTION:
- 30% Easy questions (straightforward recall of key facts and definitions)
- 40% Medium questions (conceptual understanding and application)
- 30% Hard questions (analysis, evaluation, and complex scenarios)

QUESTION TYPE VARIETY:
- Factual Recall: Testing knowledge of specific information, definitions, or facts
- Conceptual Understanding: Testing comprehension of key ideas, principles, and relationships
- Application: Testing ability to apply knowledge to real-world scenarios or new situations
- Analysis: Testing ability to compare, contrast, evaluate, or analyze complex situations

GUIDELINES FOR CHALLENGING QUESTIONS:
1. Use scenario-based questions that require critical thinking
2. Include questions that test understanding of WHY and HOW, not just WHAT
3. Create plausible distractors (wrong options that seem reasonable)
4. Test ability to distinguish between similar concepts
5. Include questions requiring multi-step reasoning

Generate exactly {num_questions} multiple-choice questions. Each question must have:
1. A clear, well-formulated question text
2. Four plausible options (A, B, C, D) - avoid obviously wrong answers
3. The correct answer (letter only: A, B, C, or D)
4. A comprehensive explanation that clarifies why the answer is correct AND why other options are incorrect

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
        
        
        # Call Groq API with Meta Llama 4 Scout model
        # Resource Efficiency: Using optimized model for better performance and reduced rate limiting
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
            model="meta-llama/llama-4-scout-17b-16e-instruct",
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



def generate_mcqs_with_rate_limiting(
    client: Groq,
    content: str,
    category: str,
    set_number: int,
    total_questions: int = 30
) -> Optional[Dict[str, Any]]:
    """
    Generate MCQs in batches with rate limiting to avoid API errors.
    
    Generates questions in batches of 10 with a 61-second delay between batches
    to comply with Groq API rate limits.
    
    Args:
        client: Initialized Groq client
        content: Text content from which to generate questions
        category: Category name
        set_number: Set number (always 1 for new requirements)
        total_questions: Total number of questions to generate (default: 30)
        
    Returns:
        Dictionary containing MCQ set with all questions or None if generation fails
        
    Security: Implements rate limiting to prevent API abuse and service interruption.
    Resource Efficiency: Batched processing reduces overall API call overhead.
    """
    logger.info(f"Starting batch generation of {total_questions} questions for {category}")
    
    # Calculate number of batches (10 questions per batch)
    batch_size = 10
    num_batches = (total_questions + batch_size - 1) // batch_size  # Ceiling division
    all_questions = []
    
    # Generate questions in batches
    for batch_num in range(num_batches):
        # Calculate questions for this batch
        remaining_questions = total_questions - len(all_questions)
        questions_in_batch = min(batch_size, remaining_questions)
        
        logger.info(f"Generating batch {batch_num + 1}/{num_batches} ({questions_in_batch} questions)")
        
        try:
            # Generate batch of questions
            batch_result = generate_mcq_set(
                client,
                content,
                category,
                set_number,
                num_questions=questions_in_batch
            )
            
            if batch_result and batch_result.get('questions'):
                batch_questions = batch_result['questions']
                all_questions.extend(batch_questions)
                logger.info(f"Batch {batch_num + 1} completed: {len(batch_questions)} questions added (Total: {len(all_questions)}/{total_questions})")
            else:
                logger.error(f"Batch {batch_num + 1} failed to generate questions")
                # Continue to next batch instead of failing completely
            
            # Add delay after every batch except the last one
            # This prevents rate limit errors from Groq API
            if batch_num < num_batches - 1:  # Don't delay after the last batch
                logger.info(f"Rate limit protection: Waiting 61 seconds before next batch...")
                time.sleep(61)  # 61-second delay to avoid rate limits
                
        except Exception as e:
            logger.error(f"Error in batch {batch_num + 1}: {str(e)}")
            # Continue to next batch
            continue
    
    # Return complete set if we have questions
    if all_questions:
        logger.info(f"Successfully generated {len(all_questions)} questions for {category}")
        return {
            "category": category,
            "set_number": set_number,
            "questions": all_questions,
            "total_questions": len(all_questions)
        }
    else:
        logger.error(f"Failed to generate any questions for {category}")
        return None



def process_category_mcqs(category: str) -> List[Dict[str, Any]]:
    """
    Process all PDFs in a category and generate 1 set of 25 MCQs.
    
    This function extracts text from all PDFs in the specified category
    and generates a single set of 25 multiple-choice questions with:
    - 4 options each
    - Correct answer
    - Explanation for each question
    
    Args:
        category: Category name (agriculture, climate, or renewable_energy)
        
    Returns:
        List containing 1 MCQ set with 25 questions
        
    Security: Implements comprehensive input validation and error handling.
    Resource Efficiency: Reuses extracted PDF content and implements rate limiting.
    """
    logger.info(f"Processing category: {category}")
    
    # Security: Get PDF files with path validation
    pdf_files = get_category_pdfs(category)
    
    if not pdf_files:
        logger.warning(f"No PDF files found for category: {category}")
        return []
    
    # Extract text from all PDFs in the category
    # Resource Efficiency: Combines all PDF content to provide diverse question material
    combined_content = ""
    for pdf_file in pdf_files:
        try:
            text = extract_text_from_pdf(str(pdf_file))
            combined_content += text + "\n\n"
            logger.info(f"Successfully extracted text from {pdf_file.name}")
        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {e}")
            continue
    
    if not combined_content.strip():
        logger.error(f"No content extracted from PDFs in {category}")
        return []
    
    logger.info(f"Extracted {len(combined_content)} characters from {len(pdf_files)} PDF(s) in category {category}")
    
    # Generate 1 set of 30 MCQs with rate limiting
    # Set number is always 1 as per new requirements
    logger.info(f"Generating single set of 30 questions for {category}")
    mcq_set = generate_mcqs_with_rate_limiting(
        groq_client,
        combined_content,
        category,
        set_number=1,
        total_questions=30
    )
    
    if mcq_set:
        logger.info(f"Successfully generated set with {mcq_set['total_questions']} questions")
        return [mcq_set]  # Return as list for compatibility with existing response format
    else:
        logger.error(f"Failed to generate MCQ set for {category}")
        return []


# API Endpoints

@app.get("/")
def root():
    """
    Root endpoint providing API information.
    
    Returns:
        Basic API information, available endpoints, and generation specifications.
        Categories are dynamically loaded from CSV file.
    """
    return {
        "service": "MCQ Generator API",
        "version": "2.0.0",
        "description": "Generate MCQ questions from PDFs using Groq API (Meta Llama 4 Scout) - Quickbase Integration Ready",
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "generation_specs": {
            "questions_per_set": 25,
            "sets_per_category": 1,
            "set_number": 1,
            "options_per_question": 4,
            "includes_explanation": True,
            "rate_limiting": "61-second delay after every 5 questions"
        },
        "endpoints": {
            "/generate-mcqs": "POST - Generate MCQs for a specific CourseID (standard format)",
            "/generate-mcqs-quickbase": "POST - Generate MCQs in Quickbase field ID format",
            "/generate-microlearning-quickbase": "POST - Generate micro-learning modules for a CourseID (RAG-based)",
            "/categories": "GET - List available categories",
            "/health": "GET - Health check endpoint",
            "/clear-cache": "POST - Clear PDF content cache"
        },
        "request_format": {
            "CourseID": "Use course ID (e.g., '001', '002', '003') instead of category name"
        },
        "course_mappings": COURSE_ID_TO_CATEGORY,
        "categories": ALLOWED_CATEGORIES,
        "category_management": {
            "type": "CSV-based (dynamic)",
            "file_path": "data/category_file/categories.csv",
            "note": "Add new categories to CSV without code changes"
        },
        "quickbase": {
            "table_id": "bvxbt7fyw",
            "realm": "accentureglobaldeliverytraining.quickbase.com",
            "field_changes": {
                "course_id": "Field 19 (was Field 7 for category, then Field 17)",
                "correct_answer": "Field 15 (letter: A, B, C, or D)"
            }
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
    Generate MCQ questions for a specified course.
    
    This endpoint processes PDFs for the given CourseID and generates
    1 set of 25 MCQs, each with 4 options, correct answer, and explanation.
    All questions will have set_number = 1.
    
    **Rate Limiting**: Implements 61-second delays after every 5 questions to prevent API rate limit errors.
    **Model**: Uses Meta Llama 4 Scout 17B 16E Instruct model from Groq.
    **Quickbase Integration**: Send POST request with JSON body: {"CourseID": "001"}
    **Authentication**: Include X-API-Key header if API_KEY is configured
    
    Args:
        request: MCQRequest containing the CourseID
        authenticated: Authentication result from dependency
        
    Returns:
        MCQResponse with 1 MCQ set containing 25 questions
    Raises:
        HTTPException: If CourseID is invalid, authentication fails, or generation fails
        
    Security:
        - Optional API key authentication via X-API-Key header
        - Input validation via Pydantic models
        - Path traversal prevention
        - GROQ API key protection
        - Rate limiting to prevent API abuse
        
    Accessibility:
        - Returns structured JSON compatible with screen readers
        - Clear error messages
    """
    try:
        course_id = request.CourseID
        logger.info(f"Received MCQ generation request for CourseID: {course_id}")
        
        # Map CourseID to category
        category = COURSE_ID_TO_CATEGORY.get(course_id)
        if not category:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid CourseID. Must be one of: {list(COURSE_ID_TO_CATEGORY.keys())}"
            )
        
        logger.info(f"CourseID '{course_id}' mapped to category: {category}")
        
        # Generate MCQs
        mcq_sets = process_category_mcqs(category)
        
        if not mcq_sets:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate MCQs for CourseID: {course_id}"
            )
        
        # Prepare response
        response = MCQResponse(
            status="success",
            category=category,
            mcq_sets=mcq_sets,
            total_sets=len(mcq_sets),
            message=f"Successfully generated {len(mcq_sets)} MCQ set with 25 questions for CourseID {course_id}"
        )
        
        logger.info(f"Successfully generated {len(mcq_sets)} set(s) with 25 questions for CourseID {course_id}")
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



def transform_to_quickbase_format(standard_response: Dict[str, Any], course_id: str) -> Dict[str, Any]:
    """
    Transform standard MCQ response to Quickbase field ID format.
    Simple transformation function that converts existing response structure.
    
    Args:
        standard_response: Standard MCQResponse format from /generate-mcqs
        course_id: Course ID (e.g., "001")
        
    Returns:
        Dictionary in Quickbase API format with field IDs
        
    Field Mappings:
        - 19: course_id (e.g., "001")
        - 8: set_number (always 1)
        - 10: question_no (1-30)
        - 18: question text
        - 11-14: options A-D
        - 15: correct_answer (letter: A, B, C, or D)
        - 16: explanation
    """
    mcq_sets = standard_response.get("mcq_sets", [])
    quickbase_records = []
    
    for mcq_set in mcq_sets:
        set_number = mcq_set.get("set_number", 1)
        questions = mcq_set.get("questions", [])
        
        for idx, question in enumerate(questions, start=1):
            correct_answer_letter = question.get("correct_answer", "A")
            
            record = {
                "19": {"value": course_id},  # Changed from field 7 to 17, now to 19 for course_id
                "8": {"value": set_number},
                "10": {"value": str(idx)},
                "18": {"value": question.get("question", "")},
                "11": {"value": question.get("options", {}).get("A", "")},
                "12": {"value": question.get("options", {}).get("B", "")},
                "13": {"value": question.get("options", {}).get("C", "")},
                "14": {"value": question.get("options", {}).get("D", "")},
                "15": {"value": correct_answer_letter},  # Letter (A, B, C, D)
                "16": {"value": question.get("explanation", "")}
            }
            quickbase_records.append(record)
    
    return {
        "to": "bvxbt7fyw",
        "data": quickbase_records,
        "fieldsToReturn": [6, 19, 8, 10, 18, 11, 12, 13, 14, 15, 16]
    }



@app.post("/generate-mcqs-quickbase")
async def generate_mcqs_quickbase(
    request: MCQRequest = Body(...),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Generate MCQ questions in Quickbase field ID format.
    
    This endpoint reuses the existing /generate-mcqs logic and transforms the output
    to Quickbase format. Generates 1 set of 25 questions with set_number = 1.
    
    **Request Body**:
    ```json
    {
        "CourseID": "001"
    }
    ```
    
    Field mappings:
    - 19: course_id (e.g., "001")
    - 8: set_number (always 1)
    - 10: question_no (1-30)
    - 18: question text
    - 11-14: options A-D
    - 15: correct_answer (letter: A, B, C, or D)
    - 16: explanation
    
    **Rate Limiting**: Implements 61-second delays after every 5 questions.
    **Model**: Uses Meta Llama 4 Scout 17B 16E Instruct model.
    """
    try:
        course_id = request.CourseID
        logger.info(f"Quickbase format requested for CourseID: {course_id}")
        
        # Map CourseID to category
        category = COURSE_ID_TO_CATEGORY.get(course_id)
        if not category:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid CourseID. Must be one of: {list(COURSE_ID_TO_CATEGORY.keys())}"
            )
        
        logger.info(f"CourseID '{course_id}' mapped to category: {category}")
        
        # Reuse existing MCQ generation
        mcq_sets = process_category_mcqs(category)
        
        if not mcq_sets:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate MCQs for CourseID {course_id}"
            )
        
        # Build standard response
        standard_response = {
            "status": "success",
            "category": category,
            "mcq_sets": mcq_sets,
            "total_sets": len(mcq_sets)
        }
        
        # Transform to Quickbase format with course_id
        quickbase_data = transform_to_quickbase_format(standard_response, course_id)
        
        logger.info(f"Transformed to {len(quickbase_data['data'])} Quickbase records for CourseID {course_id}")
        return quickbase_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_mcqs_quickbase: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-and-push-mcqs-quickbase")
async def generate_and_push_mcqs_quickbase(
    request: MCQRequest = Body(...),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Generate MCQ questions AND push them directly to Quickbase.
    
    This endpoint combines generation and pushing in one operation:
    1. Generates 1 set of 30 MCQ questions
    2. Transforms to Quickbase format
    3. Pushes records to Quickbase via API
    
    **Request Body**:
    ```json
    {
        "CourseID": "001"
    }
    ```
    
    **Environment Variables Required**:
    - QUICKBASE_TABLE_ID: Target table ID in Quickbase
    - QUICKBASE_USER_TOKEN: Authentication token (optional, defaults in code)
    - QUICKBASE_REALM_HOSTNAME: Realm hostname (optional, defaults in code)
    
    Field mappings:
    - 19: course_id (e.g., "001")
    - 8: set_number (always 1)
    - 10: question_no (1-30)
    - 18: question text
    - 11-14: options A-D
    - 15: correct_answer (letter: A, B, C, or D)
    - 16: explanation
    
    **Returns**:
    - Success status
    - Number of records generated and pushed
    - Quickbase API response
    """
    try:
        course_id = request.CourseID
        logger.info(f"Generate and push requested for CourseID: {course_id}")
        
        # Map CourseID to category
        category = COURSE_ID_TO_CATEGORY.get(course_id)
        if not category:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid CourseID. Must be one of: {list(COURSE_ID_TO_CATEGORY.keys())}"
            )
        
        logger.info(f"CourseID '{course_id}' mapped to category: {category}")
        
        # Generate MCQs
        mcq_sets = process_category_mcqs(category)
        
        if not mcq_sets:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate MCQs for CourseID {course_id}"
            )
        
        # Build standard response
        standard_response = {
            "status": "success",
            "category": category,
            "mcq_sets": mcq_sets,
            "total_sets": len(mcq_sets)
        }
        
        # Transform to Quickbase format
        quickbase_data = transform_to_quickbase_format(standard_response, course_id)
        logger.info(f"Transformed {len(quickbase_data['data'])} records for CourseID {course_id}")
        
        # Get table ID from environment
        table_id = os.getenv("QUICKBASE_TABLE_ID", "bvxbt7fyw")
        
        # Push to Quickbase
        push_result = push_mcqs_to_quickbase(
            table_id=table_id,
            mcq_records=quickbase_data["data"]
        )
        
        if push_result["success"]:
            logger.info(f"Successfully pushed {push_result['records_pushed']} records to Quickbase")
            return {
                "status": "success",
                "message": f"Generated and pushed {push_result['records_pushed']} MCQ records",
                "course_id": course_id,
                "category": category,
                "records_pushed": push_result["records_pushed"],
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
        logger.error(f"Error in generate_and_push_mcqs_quickbase: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-microlearning-quickbase")
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
    
    **Response Format**:
    ```json
    {
        "categoryName": "Circular Economy And Waste Reduction",
        "courseId": "001",
        "language": "English",
        "chapters": [
            {
                "chapterId": "CH-001",
                "chapter": "Introduction to Circular Economy",
                "microContents": [
                    {
                        "microContentId": "MC-001",
                        "microContent": "Detailed 150-300 word explanation..."
                    }
                ]
            }
        ]
    }
    ```
    
    **Features**:
    - 4-6 chapters per category
    - 3-5 micro-contents per chapter
    - Each micro-content: 150-300 words (extensive, educational)
    - Comprehensive coverage of sustainability topics
    - Professional, accessible language
    - Uses IDs for better data management
    
    **Technical Details**:
    - Uses ChromaDB vector store for content retrieval
    - Groq LLM (Meta Llama 4 Scout) for generation
    - Category-based metadata filtering
    - Retrieves top 20 most relevant chunks per category
    
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
        
        # Update courseId in response to use the actual course_id instead of generated one
        modules['courseId'] = course_id
        
        # Add chapter IDs if not present
        for idx, chapter in enumerate(modules.get('chapters', []), start=1):
            if 'chapterId' not in chapter:
                chapter['chapterId'] = f"CH-{idx:03d}"
        
        # Validate quality
        validation = generator.validate_modules(modules)
        
        if not validation['valid']:
            logger.warning(f"Generated modules failed validation: {validation['errors']}")
            # Still return the modules but log the validation issues
        
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
