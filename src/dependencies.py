"""
Shared Dependencies and Configuration

This module contains shared dependencies, configuration, and utilities
used across multiple routers.

Security: Implements API key validation and secure configuration loading.
Resource Efficiency: Singleton patterns for expensive operations.
"""

import os
import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from groq import Groq
from fastapi import Header, HTTPException
# Lazy import of microlearning_generator to avoid circular dependency

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
DATA_BASE_PATH = Path(__file__).parent.parent / "data"
CATEGORY_FILE_PATH = DATA_BASE_PATH / "category_file" / "categories.csv"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_KEY = os.getenv("API_KEY")  # Optional API key for securing the endpoint

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Dynamic category loading
ALLOWED_CATEGORIES: List[str] = []
COURSE_ID_TO_CATEGORY: Dict[str, str] = {}
CATEGORY_TO_COURSE_ID: Dict[str, str] = {}

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

# Cache for PDF content
pdf_content_cache: Dict[str, str] = {}

# Microlearning generator (lazy loading)
_microlearning_generator = None  # Type will be Optional[MicrolearningGenerator]


def normalize_category_name(category_name: str) -> str:
    """
    Convert category display name to folder name format.
    
    Example: "Circular Economy & Waste Reduction" -> "circular_economy_and_waste_reduction"
    """
    return category_name.lower().replace(' & ', '_and_').replace(' ', '_')


def load_categories_from_csv() -> List[str]:
    """
    Load active categories from CSV file and build course_id to category mappings.
    
    Returns:
        List of active category folder names
        
    Security: Validates CSV content and filters only active categories.
    """
    global COURSE_ID_TO_CATEGORY, CATEGORY_TO_COURSE_ID, ALLOWED_CATEGORIES
    
    try:
        if not CATEGORY_FILE_PATH.exists():
            logger.error(f"Category file not found at {CATEGORY_FILE_PATH}")
            raise FileNotFoundError(f"categories.csv not found at {CATEGORY_FILE_PATH}")
        
        categories = set()
        course_mappings = {}
        
        with open(CATEGORY_FILE_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('active', '').lower() == 'true':
                    category_display_name = row.get('category_name', '').strip()
                    course_id = row.get('course_id', '').strip()
                    
                    if category_display_name and course_id:
                        category_folder_name = normalize_category_name(category_display_name)
                        categories.add(category_folder_name)
                        
                        if course_id not in course_mappings:
                            course_mappings[course_id] = category_folder_name
                            logger.info(f"Mapped CourseID '{course_id}' -> '{category_folder_name}'")
        
        COURSE_ID_TO_CATEGORY = course_mappings
        CATEGORY_TO_COURSE_ID = {v: k for k, v in course_mappings.items()}
        ALLOWED_CATEGORIES = sorted(list(categories))
        
        # Update models.py with the mapping
        import models
        models.COURSE_ID_TO_CATEGORY = COURSE_ID_TO_CATEGORY
        
        logger.info(f"Total {len(ALLOWED_CATEGORIES)} active categories loaded")
        return ALLOWED_CATEGORIES
        
    except Exception as e:
        logger.error(f"Error loading categories from CSV: {str(e)}")
        raise ValueError(f"Failed to load categories: {str(e)}")


# Load categories at module import
try:
    load_categories_from_csv()
    logger.info(f"Categories initialized: {ALLOWED_CATEGORIES}")
except Exception as e:
    logger.error(f"Failed to initialize categories: {e}")
    ALLOWED_CATEGORIES = []


# API Key Authentication Dependency
async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> bool:
    """
    Verify API key from request header.
    
    Security: Implements optional API key authentication.
    """
    if not API_KEY:
        return True
    
    if not x_api_key or x_api_key != API_KEY:
        logger.warning("Unauthorized API access attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include X-API-Key header."
        )
    
    return True


# Microlearning Generator Dependency
def get_microlearning_generator():
    """Get or create the microlearning generator instance (singleton pattern)."""
    # Lazy import to avoid circular dependency
    from services.microlearning_generator import create_generator_from_env
    
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
