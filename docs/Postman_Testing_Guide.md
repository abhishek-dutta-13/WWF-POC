# Postman Testing Guide - WWF Learning Content Generator API

## Overview

This guide provides comprehensive instructions for testing the WWF Learning Content Generator API using Postman. The API generates MCQ questions and microlearning modules from sustainability content and automatically pushes them to Quickbase.

**API Version:** 2.0.0  
**Base URL:** http://localhost:8000 (local development)  
**Postman Collection:** `Postman_Collection_WWF_API.json`

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Importing Postman Collection](#importing-postman-collection)
3. [Starting the Local Server](#starting-the-local-server)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [Testing Workflow](#testing-workflow)
6. [Request Examples](#request-examples)
7. [Response Examples](#response-examples)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Postman** (Desktop or Web version)
- **Python 3.8+**
- **Dependencies** installed: `pip install -r requirements.txt`

### Required Configuration
Ensure your `.env` file contains:

```env
# API Keys
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key

# Quickbase Configuration
QUICKBASE_API_ENDPOINT=https://api.quickbase.com/v1/records
QUICKBASE_REALM_HOSTNAME=accentureglobaldeliverytraining.quickbase.com
QUICKBASE_USER_TOKEN=your_quickbase_token
QUICKBASE_TABLE_ID=bvxbt7fyw  # MCQ Table
QUICKBASE_MICROLEARNING_TABLE_ID=bvxji8seh  # Microlearning Table
```

### Vector Store Setup
Before testing microlearning endpoints, create the vector store:
1. Open `Notebook/01_data_ingestion_vector_store.ipynb`
2. Run all cells to ingest PDFs and create ChromaDB vector store
3. Verify `vector_store/` directory exists with data

---

## Importing Postman Collection

### Step 1: Locate the Collection File
The collection file is located at:
```
WWF/Postman_Collection_WWF_API.json
```

### Step 2: Import into Postman

**Method A: Drag & Drop**
1. Open Postman
2. Click "Import" button (top left)
3. Drag `Postman_Collection_WWF_API.json` into the window
4. Click "Import"

**Method B: File Selection**
1. Open Postman
2. Click "Import" → "Upload Files"
3. Navigate to `Postman_Collection_WWF_API.json`
4. Select and import

### Step 3: Verify Import
After import, you should see:
- **Collection Name:** "WWF Learning Content Generator API"
- **3 Folders:**
  - Health & Info (2 requests)
  - MCQ Generation (3 requests)
  - Microlearning Generation (4 requests)
- **Variables:** 4 collection variables

---

## Starting the Local Server

### Option 1: Using Batch Script (Windows - Recommended)

Double-click `run_server.cmd` or run from terminal:
```cmd
run_server.cmd
```

### Option 2: Using PowerShell

```powershell
cd "c:\Users\abhishek.j.dutta\OneDrive - Accenture\Desktop\Courses\Udemy\rag\WWF\src"
python main.py
```

### Option 3: Using Python Terminal

```python
# In python terminal
cd src
python main.py
```

### Verify Server is Running

You should see output like:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Access these URLs to confirm:
- API Info: http://localhost:8000/
- Health: http://localhost:8000/health
- Swagger Docs: http://localhost:8000/docs

---

## API Endpoints Reference

### 1. Health & Information Endpoints

#### GET `/`
**Purpose:** Get API information, available endpoints, and configuration

**Request:**
```
GET http://localhost:8000/
```

**No body required**

**Response:** Complete API documentation including endpoints, field mappings, and architecture

---

#### GET `/health`
**Purpose:** Health check to verify server status

**Request:**
```
GET http://localhost:8000/health
```

**No body required**

**Response:**
```json
{
  "status": "healthy",
  "service": "WWF Learning Content Generator API",
  "version": "2.0.0",
  "groq_api_configured": true,
  "categories_loaded": 3,
  "course_mappings_loaded": 3
}
```

---

### 2. MCQ Generation Endpoints

#### POST `/generate-mcqs-quickbase`
**Purpose:** Generate MCQ questions and push to Quickbase

**Request:**
```http
POST http://localhost:8000/generate-mcqs-quickbase
Content-Type: application/json

{
  "CourseID": "001"
}
```

**Features:**
- Generates 30 MCQs
- 4 options per question
- Includes explanations
- Rate limiting: 61-second delay between batches
- Automatically pushes to Quickbase table `bvxbt7fyw`

**Course ID Mappings:**
- `001` → Circular Economy and Waste Reduction
- `002` → Sustainability Strategy and Compliance
- `003` → Sustainable Agriculture and Natural Resources

---

### 3. Microlearning Generation Endpoints

#### POST `/generate-microlearning-quickbase`
**Purpose:** Generate microlearning modules using RAG and push to Quickbase

**Request:**
```http
POST http://localhost:8000/generate-microlearning-quickbase
Content-Type: application/json

{
  "CourseID": "001"
}
```

**Features:**
- Uses RAG (Retrieval-Augmented Generation)
- Retrieves from ChromaDB vector store
- Generates 4-6 chapters per course
- Each chapter has 3-5 micro-contents
- Each micro-content: 250-400 words (ebook-style format)
- Mix of paragraphs, bullet points, and numbered lists
- Automatically pushes to Quickbase table `bvxji8seh`

**Response includes:**
- Generated microlearning modules
- Quickbase push status

---

#### POST `/generate-microlearning-modules`
**Purpose:** Generate microlearning modules WITHOUT pushing to Quickbase

**Request:**
```http
POST http://localhost:8000/generate-microlearning-modules
Content-Type: application/json

{
  "CourseID": "001"
}
```

**Use Case:** Preview content before pushing to Quickbase

---

## Testing Workflow

### Recommended Testing Order

#### Phase 1: Verify Server Health
1. **Health Check** (`GET /health`)
   - Confirms server is running
   - Verifies configuration loaded
   - Expected: `status: "healthy"`

2. **API Info** (`GET /`)
   - Reviews all endpoints
   - Checks course mappings
   - Validates Quickbase configuration

#### Phase 2: Test MCQ Generation
3. **Generate MCQs - Course 001** (`POST /generate-mcqs-quickbase`)
   - Tests MCQ generation pipeline
   - Verifies Groq LLM integration
   - Confirms Quickbase push
   - Expected time: ~2-3 minutes (due to rate limiting)

4. **Verify in Quickbase**
   - Check table `bvxbt7fyw`
   - Confirm 30 new records
   - Validate field mapping

#### Phase 3: Test Microlearning Generation
5. **Generate Microlearning - Course 001** (`POST /generate-microlearning-quickbase`)
   - Tests RAG retrieval from vector store
   - Verifies OpenAI embeddings
   - Confirms Groq LLM generation
   - Tests Quickbase push
   - Expected time: ~1-2 minutes

6. **Verify in Quickbase**
   - Check table `bvxji8seh`
   - Confirm records (typically 15-25 depending on chapters/content)
   - Validate field mapping

#### Phase 4: Test All Courses
7. Repeat for Course 002 and 003
8. Test preview endpoint (no Quickbase push)

---

## Request Examples

### Example 1: Health Check

**Request:**
```http
GET http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "WWF Learning Content Generator API",
  "version": "2.0.0",
  "groq_api_configured": true,
  "categories_loaded": 3,
  "course_mappings_loaded": 3
}
```

**Status Code:** `200 OK`

---

### Example 2: Generate MCQs

**Request:**
```http
POST http://localhost:8000/generate-mcqs-quickbase
Content-Type: application/json

{
  "CourseID": "001"
}
```

**Expected Response:**
```json
{
  "mcqs": {
    "course_id": "001",
    "category": "Circular Economy and Waste Reduction",
    "set_number": 1,
    "total_questions": 30,
    "questions": [
      {
        "question_no": 1,
        "question": "What is the primary goal of circular economy?",
        "option_a": "Increase linear production",
        "option_b": "Eliminate waste and keep materials in use",
        "option_c": "Reduce employment",
        "option_d": "Maximize single-use products",
        "correct_answer": "B",
        "explanation": "The circular economy aims to eliminate waste by keeping materials in continuous use..."
      }
    ]
  },
  "quickbase_push": {
    "success": true,
    "records_pushed": 30,
    "table_id": "bvxbt7fyw"
  }
}
```

**Status Code:** `200 OK`

---

### Example 3: Generate Microlearning

**Request:**
```http
POST http://localhost:8000/generate-microlearning-quickbase
Content-Type: application/json

{
  "CourseID": "001"
}
```

**Expected Response:**
```json
{
  "microlearning_modules": {
    "categoryName": "Circular Economy And Waste Reduction",
    "courseId": "001",
    "language": "English",
    "chapters": [
      {
        "chapter": "Introduction to Circular Economy",
        "microContents": [
          {
            "microContentId": "MC-001",
            "microContent": "The circular economy represents a fundamental shift in how we approach resource management. Unlike the traditional linear model of 'take-make-dispose,' it focuses on designing out waste and keeping materials in use for as long as possible.\n\n**Key Principles:**\n• Design products for longevity and reusability\n• Maintain materials at their highest value through repair and refurbishment\n• Regenerate natural systems through sustainable practices\n\nOrganizations implementing circular economy principles have seen significant benefits..."
          }
        ]
      }
    ]
  },
  "quickbase_push": {
    "success": true,
    "records_pushed": 20,
    "table_id": "bvxji8seh"
  }
}
```

**Status Code:** `200 OK`

---

## Response Examples

### Success Response (200 OK)

All successful API calls return:
- **Status Code:** `200 OK`
- **Content-Type:** `application/json`
- **Body:** JSON with generated content and push status

---

### Error Responses

#### 400 Bad Request - Invalid CourseID
```json
{
  "detail": "Invalid CourseID. Allowed CourseIDs: 001, 002, 003"
}
```

**Cause:** CourseID not in allowed list

**Fix:** Use valid CourseID (001, 002, or 003)

---

#### 500 Internal Server Error - Generation Failed
```json
{
  "detail": "Failed to generate micro-learning modules: No content found for category: unknown_category"
}
```

**Common Causes:**
1. Vector store not created
2. No PDFs in category folder
3. Groq API key invalid
4. OpenAI API key invalid

**Fix:**
1. Run `Notebook/01_data_ingestion_vector_store.ipynb`
2. Verify PDFs exist in `data/{category}/*.pdf`
3. Check `.env` file has valid API keys

---

#### 500 Internal Server Error - Quickbase Push Failed
```json
{
  "detail": "Generated modules successfully but failed to push to Quickbase: HTTP 401: Unauthorized"
}
```

**Cause:** Invalid Quickbase credentials

**Fix:** Verify in `.env`:
- `QUICKBASE_USER_TOKEN` is valid
- `QUICKBASE_REALM_HOSTNAME` is correct

---

## Troubleshooting

### Server Won't Start

**Error:** `No module named 'fastapi'`

**Solution:**
```cmd
pip install -r requirements.txt
```

---

**Error:** `GROQ_API_KEY not found in environment variables`

**Solution:** Check `.env` file contains:
```env
GROQ_API_KEY=your_groq_api_key
```

---

### Request Timeout

**Symptom:** Request takes too long and times out

**Cause:** MCQ generation has intentional rate limiting (61 seconds between batches)

**Solution:** 
- Wait for completion (2-3 minutes for MCQs)
- Check server logs for progress
- This is normal behavior

---

### Vector Store Not Found

**Error:** `No collection found: wwf_knowledge_base`

**Solution:**
1. Run `Notebook/01_data_ingestion_vector_store.ipynb`
2. Complete all cells to create vector store
3. Verify `vector_store/` directory exists with `chroma.sqlite3`

---

### Quickbase Push Fails

**Error:** `HTTP 401: Unauthorized`

**Solution:** Verify Quickbase credentials:
```env
QUICKBASE_USER_TOKEN=your_valid_token
QUICKBASE_REALM_HOSTNAME=accentureglobaldeliverytraining.quickbase.com
```

---

**Error:** `HTTP 403: Forbidden`

**Solution:** Check Quickbase user has permission to write to:
- Table ID `bvxbt7fyw` (MCQs)
- Table ID `bvxji8seh` (Microlearning)

---

## Collection Variables

The Postman collection includes these variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `base_url` | `http://localhost:8000` | API base URL |
| `course_id_circular_economy` | `001` | Circular Economy course ID |
| `course_id_sustainability_strategy` | `002` | Sustainability Strategy course ID |
| `course_id_agriculture` | `003` | Sustainable Agriculture course ID |

**Usage in Requests:**
```
{{base_url}}/generate-mcqs-quickbase

Body:
{
  "CourseID": "{{course_id_circular_economy}}"
}
```

---

## Best Practices

### Testing Order
1. ✅ Start with health check
2. ✅ Test one course at a time
3. ✅ Verify Quickbase after each test
4. ✅ Use preview endpoint before pushing

### Performance Tips
- **MCQ Generation:** Allow 2-3 minutes (rate limiting)
- **Microlearning:** Allow 1-2 minutes (LLM generation)
- **Concurrent Requests:** Avoid - process one at a time

### Monitoring
- Check server logs in terminal for detailed progress
- Review response JSON for validation errors
- Verify Quickbase records after each push

---

## Quickbase Field Mappings

### MCQ Table (bvxbt7fyw)

| Field ID | Field Name | Type | Example |
|----------|------------|------|---------|
| 19 | Course ID | Text | "001" |
| 8 | Set Number | Number | 1 |
| 10 | Question No | Number | 1 |
| 18 | Question | Text | "What is circular economy?" |
| 11 | Option A | Text | "Linear production" |
| 12 | Option B | Text | "Eliminate waste" |
| 13 | Option C | Text | "Reduce employment" |
| 14 | Option D | Text | "Single-use products" |
| 15 | Correct Answer | Text | "B" |
| 16 | Explanation | Rich Text | "The circular economy aims to..." |

### Microlearning Table (bvxji8seh)

| Field ID | Field Name | Type | Example |
|----------|------------|------|---------|
| 12 | Course ID | Text | "001" |
| 20 | Micro Content ID | Text | "MC-001" |
| 8 | Language | Text | "English" |
| 6 | Chapter | Text | "Introduction to Circular Economy" |
| 7 | Content | Rich Text | "The circular economy represents..." |

---

## Additional Resources

- **Local Server Guide:** `QUICK_START.md`
- **Detailed Setup:** `Server_Guide.md`
- **API Documentation (Live):** http://localhost:8000/docs
- **Configuration Checker:** Run `python check_config.py`

---

## Support

### Common Issues
1. Check server logs in terminal
2. Verify `.env` configuration
3. Ensure vector store exists
4. Confirm Quickbase credentials

### Quick Diagnostics
```cmd
python check_config.py
```

This validates:
- Environment variables
- Python packages
- Project structure
- Vector store

---

**Document Version:** 1.0  
**Last Updated:** April 7, 2026  
**API Version:** 2.0.0
