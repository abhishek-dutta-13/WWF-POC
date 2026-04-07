# 🚀 Quick Start Guide - Micro-Learning Module Generator

## ⚡ 5-Minute Setup

### 1. Install Dependencies (2 minutes)

```powershell
cd "C:\Users\abhishek.j.dutta\OneDrive - Accenture\Desktop\Courses\Udemy\rag\WWF"
pip install -r requirements.txt
```

### 2. Create Vector Store (5-10 minutes)

```powershell
# Start Jupyter
jupyter notebook

# Open and run ALL cells in:
Notebook/01_data_ingestion_vector_store.ipynb
```

**Wait for**: `✅ VECTOR STORE CREATION COMPLETE!`

### 3. Test Locally (30 seconds)

```powershell
# Terminal 1: Start API
cd src
uvicorn mcq_api_service:app --reload --port 8000

# Terminal 2: Test endpoint
curl --location "http://localhost:8000/generate-microlearning-quickbase" --header "Content-Type: application/json" --data "{\"category\":\"circular_economy_and_waste_reduction\"}"
```

**✅ Done!** You should see JSON with chapters and micro-contents.

---

## 📡 API Commands Reference

### All Available Endpoints

```powershell
# Health check
curl http://localhost:8000/health

# List all endpoints and categories
curl http://localhost:8000/

# Get available categories
curl http://localhost:8000/categories
```

### MCQ Generation

```powershell
# Standard format
curl --location "http://localhost:8000/generate-mcqs" \
  --header "Content-Type: application/json" \
  --data '{
    "category": "circular_economy_and_waste_reduction"
  }'

# Quickbase format
curl --location "http://localhost:8000/generate-mcqs-quickbase" \
  --header "Content-Type: application/json" \
  --data '{
    "category": "circular_economy_and_waste_reduction"
  }'
```

### Micro-Learning Generation (NEW)

```powershell
# Local
curl --location "http://localhost:8000/generate-microlearning-quickbase" \
  --header "Content-Type: application/json" \
  --data '{
    "category": "circular_economy_and_waste_reduction"
  }'

# Production (Render)
curl --location "https://wwf-poc.onrender.com/generate-microlearning-quickbase" \
  --header "Content-Type: application/json" \
  --header "X-API-Key: your_api_key_here" \
  --data '{
    "category": "circular_economy_and_waste_reduction"
  }'
```

---

## 📋 All Categories

Copy-paste ready commands for all categories:

### Category 1: Circular Economy and Waste Reduction

```powershell
curl --location "http://localhost:8000/generate-microlearning-quickbase" \
  --header "Content-Type: application/json" \
  --data '{
    "category": "circular_economy_and_waste_reduction"
  }'
```

### Category 2: Sustainability Strategy and Compliance

```powershell
curl --location "http://localhost:8000/generate-microlearning-quickbase" \
  --header "Content-Type: application/json" \
  --data '{
    "category": "sustainability_strategy_and_compliance"
  }'
```

### Category 3: Sustainable Agriculture and Natural Resources

```powershell
curl --location "http://localhost:8000/generate-microlearning-quickbase" \
  --header "Content-Type: application/json" \
  --data '{
    "category": "sustainable_agriculture_and_natural_resources"
  }'
```

---

## 🔍 Testing Checklist

After setup, verify each step:

- [ ] Vector store created: `dir vector_store` shows files
- [ ] API starts without errors
- [ ] Health check returns "healthy"
- [ ] Categories endpoint shows 3 categories
- [ ] Micro-learning generates 4-6 chapters
- [ ] Each micro-content is 150-300 words
- [ ] JSON structure matches requirements
- [ ] Response time is 5-15 seconds (after first request)

---

## 📊 Expected Outputs

### Health Check Response

```json
{
  "status": "healthy",
  "service": "MCQ Generator API",
  "groq_api_configured": true
}
```

### Categories Response

```json
{
  "categories": [
    "circular_economy_and_waste_reduction",
    "sustainability_strategy_and_compliance",
    "sustainable_agriculture_and_natural_resources"
  ],
  "total": 3
}
```

### Micro-Learning Response Structure

```json
{
  "categoryName": "Circular Economy And Waste Reduction",
  "courseId": "COURSE-CIR-001",
  "language": "English",
  "chapters": [
    {
      "chapter": "Introduction to Circular Economy",
      "microContents": [
        {
          "microContentId": "MC-001",
          "microContent": "150-300 word detailed explanation..."
        },
        {
          "microContentId": "MC-002",
          "microContent": "Another detailed explanation..."
        }
      ]
    }
  ]
}
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```env
# Required for all endpoints
GROQ_API_KEY=gsk_your_actual_groq_api_key_here

# Optional - for securing endpoints
API_KEY=your_secure_api_key_here

# Optional - custom vector store path
VECTOR_STORE_PATH=C:\Users\abhishek.j.dutta\OneDrive - Accenture\Desktop\Courses\Udemy\rag\WWF\vector_store

# Optional - CORS origins (comma-separated)
ALLOWED_ORIGINS=*
```

---

## 🐛 Common Issues & Quick Fixes

### Issue: "GROQ_API_KEY not found"

```powershell
# Check .env file exists
dir .env

# Verify content
notepad .env

# Should contain:
# GROQ_API_KEY=gsk_...
```

### Issue: "No module named 'chromadb'"

```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: "No content found for category"

```powershell
# Re-run data ingestion notebook
jupyter notebook
# Open: Notebook/01_data_ingestion_vector_store.ipynb
# Run all cells
```

### Issue: Port 8000 already in use

```powershell
# Use different port
uvicorn mcq_api_service:app --reload --port 8001

# Or kill existing process
Get-Process -Name "python" | Stop-Process -Force
```

### Issue: Response too slow (> 30 seconds)

**First request is always slower** (loads models). Subsequent requests should be 5-15 seconds.

If still slow:
- Reduce `top_k_chunks` to 15
- Reduce `max_chunks_for_llm` to 10
- Check internet connection (LLM API call)

---

## 📈 Performance Benchmarks

| Metric | Value |
|--------|-------|
| Vector store creation | 5-10 minutes (one-time) |
| Cold start (first request) | 8-15 seconds |
| Warm request | 5-10 seconds |
| Vector retrieval | ~1 second |
| LLM generation | 4-9 seconds |
| Memory usage | 2-4 GB |
| Vector store size | 50-200 MB |

---

## 🎯 Next Steps

1. **Test all three categories** to verify generation quality
2. **Review generated content** in the testing notebook
3. **Customize prompts** if needed for specific tone
4. **Deploy to Render** for production use
5. **Integrate with Quickbase** using the API

---

## 📚 Documentation Links

- **Full Setup Guide**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Detailed Documentation**: [MICROLEARNING_README.md](MICROLEARNING_README.md)
- **Main README**: [README.md](README.md)
- **Quickbase Integration**: [QUICKBASE.md](QUICKBASE.md)

---

## 💡 Pro Tips

✅ **Warm up the API** on startup: Make a test request to initialize models  
✅ **Cache results** for frequently requested categories  
✅ **Monitor logs** for quality validation warnings  
✅ **Version your vector store** when updating PDFs  
✅ **Use the testing notebook** before deploying changes  

---

**Ready to go!** 🚀

Start with the vector store creation, then test locally. Deploy when you're confident in the results.
