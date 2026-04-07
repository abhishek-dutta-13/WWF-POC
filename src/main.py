"""
Main Application Entry Point

This is the main FastAPI application that includes all routers.

Security: Implements CORS and API key authentication.
Architecture: Router-based modular design for better organization.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

# Import routers
from routers import mcq_router, microlearning_router, chatbot_router
from dependencies import GROQ_API_KEY, ALLOWED_ORIGINS, COURSE_ID_TO_CATEGORY, ALLOWED_CATEGORIES

# Import chatbot database
from chatbot.database import init_db, get_db, get_database_info

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
    title="WWF Learning Content Generator API",
    description="Generate MCQ questions and micro-learning modules from PDFs using Groq API - Quickbase Integration Ready",
    version="2.0.0"
)


# ==================== Startup Event ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    logger.info("🚀 Starting WWF Learning Content Generator API...")
    
    # Initialize database (create tables if they don't exist)
    try:
        init_db()
        db_info = get_database_info()
        logger.info(f"📊 Database initialized: {db_info['database_type']}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
    
    logger.info("✅ Application startup complete")


# ==================== CORS Configuration ====================

logger.info("Configuring CORS middleware")
if ALLOWED_ORIGINS == ["*"]:
    logger.warning("CORS is set to allow all origins. Set ALLOWED_ORIGINS in .env for production")

# Add CORS middleware to allow cross-origin requests from Quickbase and other clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Origins allowed to make requests (configured via .env)
    allow_credentials=True,  # Allow cookies and authentication headers
    allow_methods=["POST", "GET", "OPTIONS"],  # HTTP methods permitted
    allow_headers=["*"],  # Allow all headers including X-API-Key for authentication
)

# Include routers

app.include_router(mcq_router.router)
app.include_router(microlearning_router.router)
app.include_router(chatbot_router.router)

# Root endpoint
@app.get("/")
def root():
    """
    Root endpoint providing API information.
    
    Returns:
        Basic API information, available endpoints, and generation specifications.
    """
    return {
        "service": "WWF Learning Content Generator API",
        "version": "2.0.0",
        "description": "Generate MCQ questions and micro-learning modules from PDFs using Groq API (Meta Llama 4 Scout) - Quickbase Integration Ready",
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "generation_specs": {
            "mcq_questions_per_set": 30,
            "mcq_sets_per_category": 1,
            "set_number": 1,
            "options_per_question": 4,
            "includes_explanation": True,
            "rate_limiting": "61-second delay every 15 questions (2 batches total)",
            "microlearning_chapters": "4-6 per category",
            "microlearning_micro_contents": "3-5 per chapter",
            "microlearning_word_count": "150-300 words per micro-content"
        },
        "endpoints": {
            "/": "GET - This information page",
            "/health": "GET - Health check endpoint",
            "/categories": "GET - List available categories",
            "/clear-cache": "POST - Clear PDF content cache",
            "/generate-mcqs": "POST - Generate MCQs for a CourseID (standard format)",
            "/generate-mcqs-quickbase": "POST - Generate MCQs and push to Quickbase",
            "/generate-microlearning-quickbase": "POST - Generate micro-learning modules and push to Quickbase (RAG-based)",
            "/generate-microlearning-modules": "POST - Generate micro-learning modules only (no Quickbase push)",
            "/launcher": "GET - Test launcher page (simulates Quickbase button)",
            "/chat": "GET - Chatbot UI (open in browser)",
            "/chatbot/session/init": "POST - Initialize chat session",
            "/chatbot/message": "POST - Send message to chatbot",
            "/chatbot/session/{id}/history": "GET - Get chat history",
            "/chatbot/user/{id}/sessions": "GET - Get user's sessions",
            "/chatbot/download/{filename}": "GET - Download PDF export"
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
            "field_mapping": {
                "course_id": "Field 19",
                "set_number": "Field 8",
                "question_no": "Field 10",
                "question": "Field 18",
                "option_a": "Field 11",
                "option_b": "Field 12",
                "option_c": "Field 13",
                "option_d": "Field 14",
                "correct_answer": "Field 15 (letter: A, B, C, or D)",
                "explanation": "Field 16"
            }
        },
        "architecture": {
            "type": "Router-based modular design with service layer",
            "layers": {
                "routers": ["mcq_router", "microlearning_router"],
                "services": ["mcq_service (business logic)"],
                "modules": ["models (data validation)", "dependencies (config)", "utils (helpers)"]
            }
        }
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status and configuration status.
    """
    db_info = get_database_info()
    
    return {
        "status": "healthy",
        "service": "WWF Learning Content Generator API",
        "version": "2.0.0",
        "groq_api_configured": bool(GROQ_API_KEY),
        "categories_loaded": len(ALLOWED_CATEGORIES),
        "course_mappings_loaded": len(COURSE_ID_TO_CATEGORY),
        "database": {
            "type": db_info["database_type"],
            "status": "connected"
        }
    }


@app.get("/db-test")
def test_database(db: Session = Depends(get_db)):
    """
    Test database connection.
    
    Returns:
        Database connection status and test query result.
    """
    try:
        # Try a simple query to verify connection
        if "postgresql" in str(db.bind.url):
            result = db.execute("SELECT 1 as test").scalar()
            db_type = "PostgreSQL"
        else:
            result = db.execute("SELECT 1 as test").scalar()
            db_type = "SQLite"
        
        return {
            "status": "connected",
            "database_type": db_type,
            "test_query_result": result,
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Database connection failed"
        }


# ==================== Chatbot UI Serving ====================

# Mount static files for chatbot UI (optional - can be deployed separately)
chatbot_ui_path = Path(__file__).parent.parent / "chatbot-ui"
if chatbot_ui_path.exists():
    logger.info(f"Serving chatbot UI from: {chatbot_ui_path}")
    
    # Mount static files (for images, CSS, etc.)
    app.mount("/static", StaticFiles(directory=str(chatbot_ui_path)), name="static")
    
    @app.get("/chat")
    async def serve_chat_ui():
        """
        Serve the chatbot UI
        
        Access at: http://localhost:8000/chat
        Or with user context: http://localhost:8000/chat?user_id=123&name=John&location=CA&education=Science
        """
        chat_file = chatbot_ui_path / "index.html"
        if chat_file.exists():
            return FileResponse(chat_file)
        return {"error": "Chat UI not found"}
    
    @app.get("/launcher")
    async def serve_launcher():
        """
        Serve the test launcher page (simulates Quickbase button)
        
        Access at: http://localhost:8000/launcher
        
        This page allows you to test the chatbot by entering user details
        and launching the chat with those parameters (simulates Quickbase integration)
        """
        launcher_file = chatbot_ui_path / "launcher.html"
        if launcher_file.exists():
            return FileResponse(launcher_file)
        return {"error": "Launcher page not found"}
    
    @app.get("/wwf-logo-new.jpg")
    async def serve_logo():
        """Serve the WWF logo"""
        logo_file = chatbot_ui_path / "wwf-logo-new.jpg"
        if logo_file.exists():
            return FileResponse(logo_file, media_type="image/jpeg")
        return {"error": "Logo not found"}
else:
    logger.warning("Chatbot UI directory not found. Chat UI will not be available at /chat")


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
