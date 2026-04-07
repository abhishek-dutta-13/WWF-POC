# WWF Learning Content Generator API

FastAPI-based API for generating MCQ questions and micro-learning modules from PDF documents using Groq API (Meta Llama 4 Scout).

## 🏗️ Architecture

This project follows a **layered, router-based modular architecture** with clear separation of concerns:

```
src/
├── services/                    # ✨ Business Logic Layer
│   ├── __init__.py
│   └── mcq_service.py           # Core MCQ generation logic
│       ├── generate_mcq_set()
│       ├── generate_mcqs_with_rate_limiting()
│       └── process_category_mcqs()
│
├── routers/                     # API Endpoints Layer
│   ├── __init__.py
│   ├── mcq_router.py            # MCQ endpoints (imports from services/)
│   └── microlearning_router.py  # Microlearning endpoints
│
├── utils.py                     # ✅ ONLY Utility Functions
│   ├── extract_text_from_pdf()           # PDF text extraction
│   ├── get_category_pdfs()               # File listing
│   └── transform_to_quickbase_format()   # Data transformation
│
├── models.py                    # Pydantic data models
├── dependencies.py              # Shared configuration & dependencies
├── main.py                      # Application entry point
├── microlearning_generator.py   # Microlearning RAG logic
└── quickbase_client.py          # Quickbase API integration
```

---

## 📦 Layer Responsibilities

### **Services Layer** (`services/`)
- **Purpose**: Core business logic
- **Contains**: MCQ generation algorithms, rate limiting, orchestration
- **Used by**: Routers
- **Never imports from**: Routers

### **Routers Layer** (`routers/`)
- **Purpose**: API endpoints and HTTP handling
- **Contains**: FastAPI route handlers, request/response logic
- **Imports from**: Services, Models, Dependencies, Utils
- **Returns**: Pydantic model responses

### **Utils** (`utils.py`)
- **Purpose**: Generic helper/utility functions
- **Contains**: PDF processing, file operations, data transformations
- **Does NOT contain**: Business logic, LLM calls, or orchestration
- **Used by**: Services and Routers

### **Models** (`models.py`)
- **Purpose**: Data validation and serialization
- **Contains**: Pydantic models for requests and responses
- **Used by**: All layers

### **Dependencies** (`dependencies.py`)
- **Purpose**: Shared configuration and dependency injection
- **Contains**: API clients, config loading, authentication
- **Used by**: All layers

---

## 🚀 Features

### MCQ Generation
- **Difficulty Distribution**: 30% Easy, 40% Medium, 30% Hard
- **Question Types**: Conceptual, Application, Analysis, Evaluation, Scenario-based
- **Output**: 30 questions per set, 4 options each, with explanations
- **Rate Limiting**: 61-second delays every 15 questions (2 batches: 15+15)
- **Model**: Meta Llama 4 Scout 17B 16E Instruct

### Microlearning Modules
- **Approach**: RAG-based using ChromaDB vector store
- **Structure**: 4-6 chapters per category, 3-5 micro-contents per chapter
- **Word Count**: 150-300 words per micro-content
- **Output**: JSON format for Quickbase integration

---

## 📋 API Endpoints

### MCQ Endpoints
- `POST /generate-mcqs` - Generate MCQs (standard format)
- `POST /generate-mcqs-quickbase` - Generate MCQs (Quickbase format)
- `POST /generate-and-push-mcqs-quickbase` - Generate and push to Quickbase
- `GET /categories` - List available categories
- `POST /clear-cache` - Clear PDF content cache

### Microlearning Endpoint
- `POST /generate-microlearning-quickbase` - Generate microlearning module

### System Endpoints
- `GET /` - API documentation and info
- `GET /health` - Health check

---

## 🔧 Configuration

### Environment Variables (`.env`)

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Quickbase Integration
QUICKBASE_REALM_HOSTNAME=your_realm.quickbase.com
QUICKBASE_USER_TOKEN=your_user_token_here
QUICKBASE_TABLE_ID=your_table_id_here

# Optional Security
API_KEY=your_api_key_for_endpoint_authentication

# CORS Configuration (Production)
ALLOWED_ORIGINS=https://your-quickbase-domain.com,https://your-frontend.com
```

**Development**: Copy `.env.example` to `.env` and fill in your credentials.

---

## 📚 Course ID Mappings

Configured in `data/category_file/categories.csv`:

| CourseID | Category |
|----------|----------|
| 001 | circular_economy_and_waste_reduction |
| 002 | sustainability_strategy_and_compliance |
| 003 | sustainable_agriculture_and_natural_resources |

---

## 🔒 Security Features

- **Input Validation**: Pydantic models validate all inputs
- **API Key Authentication**: Optional X-API-Key header support
- **CORS Configuration**: Configurable allowed origins
- **Path Validation**: Prevents directory traversal attacks
- **Rate Limiting**: Prevents API abuse
- **Secure Configuration**: Credentials stored in environment variables only

---

## 🌱 Resource Efficiency (Green Software)

- **PDF Caching**: Extracted content cached in memory
- **Batch Processing**: Optimized API calls with rate limiting
- **Efficient Serialization**: Pydantic models for fast JSON processing
- **Smart Content Truncation**: Intelligent text sampling for large PDFs

---

## 🎯 Code Quality Standards

All code follows **Accenture's Secure Vibe Coding Guidelines**:
- Generated code marked with `# Generated by GitHub Copilot`
- Comprehensive docstrings on all functions
- Security, Accessibility, and Resource Efficiency considerations documented
- Separation of concerns via layered architecture

---

## 🚦 Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Start Server**:
   ```bash
   cd src
   python -m uvicorn main:app --reload --port 8000
   ```

4. **Test API**:
   ```bash
   curl http://127.0.0.1:8000/
   ```

---

## 📝 Example Request

```json
POST http://127.0.0.1:8000/generate-mcqs
Content-Type: application/json

{
  "CourseID": "003"
}
```

---

## 📖 Architecture Benefits

1. **Maintainability**: Clear separation makes code easy to understand and modify
2. **Testability**: Each layer can be tested independently
3. **Scalability**: New routers/services can be added without affecting existing code
4. **Reusability**: Services and utils can be used by multiple routers
5. **Team Collaboration**: Different team members can work on different layers

---

## 📄 License

Internal Accenture project for WWF learning content generation.
