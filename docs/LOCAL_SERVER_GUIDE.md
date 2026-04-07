# 🚀 Local Development Server - Quick Start Guide

## Prerequisites

- Python 3.8+
- Virtual environment activated (if using)
- Environment variables configured in `.env`
- Vector store created (run `Notebook/01_data_ingestion_vector_store.ipynb` first)

## Required Environment Variables

Make sure your `.env` file contains:

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

## 🎯 Method 1: Using run_server.cmd (Windows - Recommended)

**Easiest way to start the server:**

1. Double-click `run_server.cmd` in the root directory
   - OR open Command Prompt and run: `run_server.cmd`

2. Server will start on: **http://localhost:8000**

3. You should see:
   ```
   ============================================
   WWF Learning Content Generator API
   Starting Local Development Server...
   ============================================
   
   Starting server on http://localhost:8000
   ```

## 🐍 Method 2: Using Python Directly

```cmd
# Navigate to src directory
cd src

# Start the server
python main.py
```

## 🔍 Method 3: Using Uvicorn (Advanced)

```cmd
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag enables auto-reload on code changes (useful during development).

## 📡 Available Endpoints

Once the server is running, visit:

- **API Info**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc

### Main Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate-mcqs-quickbase` | Generate MCQs and push to Quickbase |
| POST | `/generate-microlearning-quickbase` | Generate microlearning and push to Quickbase |
| POST | `/generate-microlearning-modules` | Generate microlearning only (no push) |

## 📮 Testing with Postman

### Import the Postman Collection

1. Open Postman
2. Click "Import" button
3. Select `Postman_Collection_WWF_API.json` from the root directory
4. Collection will be imported with all pre-configured requests

### Pre-configured Requests:

**Health & Info:**
- ✅ Get API Info
- ✅ Health Check

**MCQ Generation:**
- 📝 Generate MCQs and Push to Quickbase (Course 001)
- 📝 Generate MCQs - Course 002
- 📝 Generate MCQs - Course 003

**Microlearning Generation:**
- 📚 Generate Microlearning and Push to Quickbase (Course 001)
- 📚 Generate Microlearning - Course 002
- 📚 Generate Microlearning - Course 003
- 📚 Generate Microlearning Only (No Push)

### Example Request Body:

```json
{
  "CourseID": "001"
}
```

### Course ID Mappings:

- **001** → Circular Economy and Waste Reduction
- **002** → Sustainability Strategy and Compliance
- **003** → Sustainable Agriculture and Natural Resources

## 🧪 Testing Workflow

### 1. Test Health Check
```http
GET http://localhost:8000/health
```

Expected response:
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

### 2. Test MCQ Generation
```http
POST http://localhost:8000/generate-mcqs-quickbase
Content-Type: application/json

{
  "CourseID": "001"
}
```

Expected response:
```json
{
  "mcqs": { ... },
  "quickbase_push": {
    "success": true,
    "records_pushed": 30,
    "table_id": "bvxbt7fyw"
  }
}
```

### 3. Test Microlearning Generation
```http
POST http://localhost:8000/generate-microlearning-quickbase
Content-Type: application/json

{
  "CourseID": "001"
}
```

Expected response:
```json
{
  "microlearning_modules": {
    "categoryName": "Circular Economy and Waste Reduction",
    "courseId": "001",
    "language": "English",
    "chapters": [ ... ]
  },
  "quickbase_push": {
    "success": true,
    "records_pushed": 20,
    "table_id": "bvxji8seh"
  }
}
```

## 🐛 Troubleshooting

### Server won't start

**Error**: `No module named 'fastapi'`
- **Solution**: Install dependencies: `pip install -r requirements.txt`

**Error**: `GROQ_API_KEY not found`
- **Solution**: Check `.env` file has `GROQ_API_KEY=your_key`

**Error**: `Vector store not found`
- **Solution**: Run `Notebook/01_data_ingestion_vector_store.ipynb` first to create the vector store

### 500 Internal Server Error

**Check the terminal/console for detailed error messages**

Common issues:
1. Vector store not created → Run ingestion notebook
2. API keys missing → Check `.env` file
3. Quickbase credentials invalid → Verify credentials

### Microlearning generation fails

**Error**: `No content found for category`
- **Solution**: Ensure PDFs exist in `data/{category_folder}/*.pdf`
- **Solution**: Re-run vector store creation notebook

## 📊 Monitoring Logs

The server logs will show:
- ✅ Successful requests
- ❌ Errors with details
- 🔄 Generation progress
- 📤 Quickbase push status

Example log output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
INFO:     127.0.0.1:52234 - "POST /generate-mcqs-quickbase HTTP/1.1" 200 OK
INFO:     MCQ generation requested for CourseID: 001
INFO:     Successfully pushed 30 records to Quickbase
```

## 🛑 Stopping the Server

- Press **Ctrl+C** in the terminal/command prompt
- Server will gracefully shutdown

## 🔄 Making Changes

If you modify the code:

**Method 1 (Manual Restart):**
1. Stop server (Ctrl+C)
2. Restart using `run_server.cmd`

**Method 2 (Auto-Reload):**
```cmd
cd src
uvicorn main:app --reload
```
Server will automatically restart on code changes.

## 📚 Additional Resources

- **FastAPI Docs**: http://localhost:8000/docs (Interactive API documentation)
- **ReDoc**: http://localhost:8000/redoc (Alternative API documentation)
- **Main README**: `README.md` (Project documentation)

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] All tests passing in Postman
- [ ] Vector store created and accessible
- [ ] Environment variables configured
- [ ] Quickbase credentials working
- [ ] API responses validated
- [ ] Error handling tested
- [ ] Rate limiting observed (61s delay for MCQs)
- [ ] Logs reviewed for errors

---

**Need Help?**
- Check logs in terminal for detailed error messages
- Review FastAPI docs at http://localhost:8000/docs
- Verify `.env` configuration
- Ensure all dependencies installed: `pip install -r requirements.txt`
