# 🚀 WWF Sustainability Learning Platform - API Services

Generate educational content from WWF sustainability PDFs using Groq AI (Meta Llama 4 Scout), deployed for free on Render.com.

**🎯 Available Services:**
1. **MCQ Generator** - Multiple choice questions for assessments
2. **Micro-Learning Module Generator** (NEW) - Comprehensive educational content using RAG

**📖 Documentation:**
- This file (README.md) - Complete deployment & usage guide
- [QUICKBASE.md](QUICKBASE.md) - Quickbase integration details
- [MICROLEARNING_README.md](MICROLEARNING_README.md) - Detailed micro-learning RAG implementation guide

---

## 🎓 Service 1: MCQ Generator

**✨ Key Features:**
- Generates **1 set of 25 questions** per category
- Uses **Meta Llama 4 Scout 17B 16E Instruct** model
- Implements **rate limiting** (61-second delays) to prevent API errors
- All questions have **set_number = 1**
- Each question includes 4 options, correct answer, and explanation
- **Dynamic category management** via CSV file (no code changes needed to add categories)

**📂 Current Categories:**
- Circular Economy and Waste Reduction
- Sustainability Strategy and Compliance
- Sustainable Agriculture and Natural Resources

*Categories are managed via `data/category_file/categories.csv` - add new categories without changing code!*

**🔗 Endpoints:**
- `POST /generate-mcqs` - Standard MCQ format
- `POST /generate-mcqs-quickbase` - Quickbase-ready format

---

## 📚 Service 2: Micro-Learning Module Generator (NEW - RAG-powered)

**✨ Key Features:**
- **RAG-based content retrieval** from ChromaDB vector store
- Generates **4-6 comprehensive chapters** per category
- Each micro-content is **150-300 words** (extensive, not one-liners)
- **Metadata filtering** for accurate category-specific content
- Processes **multiple large PDFs** efficiently
- **Production-ready** with quality validation

**🔗 Endpoint:**
- `POST /generate-microlearning-quickbase` - Comprehensive micro-learning modules

**📊 Output Structure:**
```json
{
  "categoryName": "Sustainability And Climate Change",
  "courseId": "COURSE-001",
  "language": "English",
  "chapters": [
    {
      "chapter": "Chapter Title",
      "microContents": [
        {
          "microContentId": "MC-001",
          "microContent": "150-300 word detailed explanation..."
        }
      ]
    }
  ]
}
```

**🏗️ Architecture:**
- **Embeddings**: HuggingFace Inference API (100% API-based, no local model loading!)
- **Vector Store**: ChromaDB persistent storage
- **Chunking**: 1000 characters with 800 character overlap
- **Retrieval**: Top-20 relevant chunks per category
- **Generation**: Groq LLM (Meta Llama 4 Scout)

**⚡ Benefits**:
- ✅ No local model loading (faster startup)
- ✅ Minimal memory usage (~100MB vs 1-2GB)
- ✅ Smaller deployment size
- ✅ Free HuggingFace Inference API tier
- ✅ Always up-to-date models

**📘 For detailed setup and usage**, see [MICROLEARNING_README.md](MICROLEARNING_README.md)  
**🔄 For API migration details**, see [HUGGINGFACE_MIGRATION_SUMMARY.md](HUGGINGFACE_MIGRATION_SUMMARY.md)

---

## 📋 Table of Contents

1. [Quick Start](#quick-start) - Deploy in 10 minutes
2. [What This Does](#what-this-does)
3. [Project Structure](#project-structure)
4. [Setup Vector Store (for Micro-Learning)](#setup-vector-store)
5. [Push to GitHub](#step-1-push-to-github)
6. [Deploy to Render](#step-2-deploy-to-render)
7. [Test Deployment](#step-3-test-deployment)
8. [Quickbase Integration](#step-4-quickbase-integration)
9. [Making Updates](#making-updates)
10. [Troubleshooting](#troubleshooting)

---

## ⚡ Quick Start

**Total Time: 15 minutes (MCQ) + 30 minutes (Micro-Learning)**

### For MCQ Generator Only:

1. **Push to GitHub**:
   ```powershell
   cd "C:\Users\abhishek.j.dutta\OneDrive - Accenture\Desktop\Courses\Udemy\rag\WWF"
   git init
   git add .
   git commit -m "MCQ Generator API"
   git remote add origin https://github.com/YOUR_USERNAME/mcq-api.git
   git push -u origin main
   ```

2. **Deploy to Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Add environment variable: `GROQ_API_KEY`
   - Click "Create Web Service"

3. **Test**: `curl https://your-app.onrender.com/health`

**Done!** Your API is live at `https://your-app.onrender.com`

---

## 🎯 What This Does

This API receives a category name and generates **1 set of 25 MCQs** with the following features:

- **Model**: Meta Llama 4 Scout 17B 16E Instruct (from Groq)
- **Questions**: 25 questions per request
- **Set Number**: Always 1
- **Rate Limiting**: 61-second delay after every 5 questions (prevents API rate limit errors)
- **Options**: 4 options (A, B, C, D) per question
- **Includes**: Correct answer and explanation for each question

**Input** (from Quickbase or any client):
```json
POST /generate-mcqs
{"category": "circular_economy_and_waste_reduction"}
```

**Output** (JSON):
```json
{
  "status": "success",
  "category": "circular_economy_and_waste_reduction",
  "total_sets": 1,
  "mcq_sets": [
    {
      "set_number": 1,
      "total_questions": 25,
      "category": "circular_economy_and_waste_reduction",
      "questions": [
        {
          "question": "What is crop rotation?",
          "options": {"A": "Option 1", "B": "Option 2", "C": "Option 3", "D": "Option 4"},
          "correct_answer": "B",
          "explanation": "Crop rotation is important because..."
        }
        // ... 24 more questions
      ]
    }
  ],
  "message": "Successfully generated 1 MCQ set with 25 questions for circular_economy_and_waste_reduction"
}
### Open PowerShell in WWF folder:

```powershell
# Navigate to your project
cd "C:\Users\abhishek.j.dutta\OneDrive - Accenture\Desktop\Courses\Udemy\rag\WWF"

# Initialize Git
git init

# Configure Git (first time only)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Check what will be pushed (.env should NOT appear!)
git status

# Add all files (except those in .gitignore)
git add .

# Commit
git commit -m "Initial commit - MCQ Generator API"
```

### Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. **Repository name**: `mcq-generator-api`
3. **Visibility**: Private (recommended) or Public
4. **DO NOT** check "Add a README" or ".gitignore"
5. Click "Create repository"

### Connect and Push

```powershell
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/mcq-generator-api.git

# Set branch name
git branch -M main

# Push to GitHub
git push -u origin main
```

**When prompted for password**: Use a [Personal Access Token](https://github.com/settings/tokens) (not your GitHub password)

**✅ Success**: Your code is on GitHub (without .env - secured by .gitignore!)

---

## 🎨 STEP 2: Deploy to Render
---

## 📁 Project Structure

```
WWF/
├── README.md                    # This file - complete guide
├── MICROLEARNING_README.md      # Detailed micro-learning documentation (NEW)
├── QUICKBASE.md                 # Quickbase integration details
├── render.yaml                  # Render deployment config (auto-detected)
├── requirements.txt             # Python dependencies (updated with RAG libraries)
├── .gitignore                   # What to exclude from Git
├── .env                         # Your secrets (local only, not pushed)
├── .env.example                 # Template for environment variables
├── data/                        # PDF documents by category
│   ├── category_file/
│   │   └── categories.csv       # Dynamic category management
│   ├── circular_economy_and_waste_reduction/
│   ├── sustainability_strategy_and_compliance/
│   └── sustainable_agriculture_and_natural_resources/
├── src/
│   ├── mcq_api_service.py       # Main FastAPI application (MCQ + Micro-learning)
│   └── microlearning_generator.py  # RAG-based micro-learning module (NEW)
├── Notebook/                    # Jupyter notebooks for setup and testing (NEW)
│   ├── 01_data_ingestion_vector_store.ipynb   # Create vector store
│   └── 02_test_microlearning_generation.ipynb # Test micro-learning
└── vector_store/                # ChromaDB persistent storage (NEW - create via notebook)
    └── chroma.sqlite3           # Vector database
```

---

## 🔧 Setup Vector Store (Required for Micro-Learning)

**⚠️ Important**: The micro-learning endpoint requires a vector store. Follow these steps to create it.

### Prerequisites

```powershell
# Install dependencies
pip install -r requirements.txt
```

### Step 1: Run Data Ingestion Notebook

1. **Start Jupyter**:
   ```powershell
   cd "C:\Users\abhishek.j.dutta\OneDrive - Accenture\Desktop\Courses\Udemy\rag\WWF"
   jupyter notebook
   ```

2. **Open and Run**: `Notebook/01_data_ingestion_vector_store.ipynb`

3. **What it does**:
   - Extracts text from all PDFs in `data/{category}/` folders
   - Chunks text with 1000 char size and 800 char overlap
   - Generates embeddings using `sentence-transformers/all-MiniLM-L6-v2`
   - Creates ChromaDB vector store at `vector_store/`
   - Stores metadata (category, source_file, chunk_index) for filtering

4. **Expected output**:
   ```
   ✅ VECTOR STORE CREATION COMPLETE!
   💾 Total chunks stored: 500+
   📁 Vector store location: C:\..\WWF\vector_store
   🎯 Collection name: wwf_knowledge_base
   ```

### Step 2: Test Micro-Learning Generation (Optional)

Run `Notebook/02_test_microlearning_generation.ipynb` to:
- Test content retrieval for each category
- Generate sample micro-learning modules
- Validate content quality
- Export JSON examples

### Step 3: Verify Vector Store

```powershell
# Check if vector store was created
dir vector_store
```

You should see files like:
- `chroma.sqlite3` (main database)
- Other ChromaDB metadata files

**✅ Vector store is now ready for use!**

The micro-learning API endpoint will automatically load the vector store when called.

---
### A. Create Web Service

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Click "Connect GitHub" (authorize if first time)
4. Select your repository: `mcq-generator-api`
5. Click "Connect"

### B. Configure Service

Fill in the configuration form:

```
Name: mcq-generator-api
Region: Oregon (US West) or nearest
Branch: main
Runtime: Python 3

Build Command: pip install -r requirements.txt
Start Command: cd src && uvicorn mcq_api_service:app --host 0.0.0.0 --port $PORT

Instance Type: Free ✅
```

**Note**: Render auto-detects `render.yaml` but you can verify/override these settings.

### C. Add Environment Variables

ScrolSTEP 3: Test Deployment

### Test 1: Health Check

```powershell
# Replace with your actual Render URL
curl https://mcq-generator-api.onrender.com/health
```

**Expected**:
```json
{
  "status": "healthy",
  "service": "MCQ Generator API",
  "groq_api_configured": true
}
```

### Test 2: Generate MCQs

**Using PowerShell**:
```powershell
$headers = @{
    "Content-Type" = "application/json"
    "X-API-Key" = "my-secret-123"
}
$body = @{category = "agriculture"} | ConvertTo-Json

Invoke-RestMethod -Uri "https://mcq-generator-api.onrender.com/generate-mcqs" `
    -Method Post -Headers $headers -Body $body
```

**Or use the test script**:
```powershell
cd src
python test_quickbase_integration.py
# Enter your Render URL when prompted
```

**Expected**: JSON with 3 MCQ sets, each containing 5 questions.

---

## 🔌 STEP 4: Quickbase Integration

See [QUICKBASE.md](QUICKBASE.md) for complete integration guide.

### Quick Setup

**Quickbase Pipeline HTTP Request**:
- **Method**: `POST`
- **URL**: `https://your-app.onrender.com/generate-mcqs`
- **Headers**:
  - `Content-Type: application/json`
  - `X-API-Key: your-secret-key` (if you set API_KEY)
- **Body**: `{"category": "{{category_field}}"}`
- **Timeout**: `180 seconds` (includes cold start)

**I_KEY` = your-secret-key (optional, for API authentication)
   - `ALLOWED_ORIGINS` = * (or your Quickbase domain)

6. **Click "Create Web Service"**

7. **Wait 2-3 minutes** for deployment to complete

8. **Your API URL will be**: `https://mcq-generator-api.onrender.com`

---

## ✅ Test Your Deployment

### Test 1: Health Check
```bash
curl https://your-app-name.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "MCQ Generator API",
  "groq_api_configured": true
}
```

### Test 2: Generate MCQs
```bash
curl -X POST "https://your-app-name.onrender.com/generate-mcqs" \
  -H� Making Updates

When you make changes to your code:

```powershell
cd "C:\Users\abhishek.j.dutta\OneDrive - Accenture\Desktop\Courses\Udemy\rag\WWF"

# Make your changes...

git add .
git commit -m "Description of changes"
git push

# Render auto-deploys! ✨ (takes 2-3 minutes)
```

---

## 📊 Render Free Tier Details

### ✅ What's Included (Forever Free)
- 750 hours/month hosting
- Automatic HTTPS/SSL
- Auto-deploy on git push
- Environment variables (encrypted)
- 512 MB RAM
- 0.1 CPU

### ⚠️ Limitations
- **Cold Start**: Service sleeps after 15 minutes of inactivity
- **First Request**: Takes 30-60 seconds to wake up after sleep
- **Solution**: Set Quickbase Pipeline timeout to 180 seconds

**Total Request Time**:
- Cold start: 30-60 seconds
- MCQ generation: 30-120 seconds
- **Total**: 60-180 seconds (acceptable for Quickbase)

---

## 🚨 Troubleshooting

### Build Failed on Render
- Check Render logs for specific error
- Verify `requirements.txt` is in root folder
- Ensure `src/mcq_api_service.py` exists

### Environment Variables Not Working
- Check variable names are spelled correctly
- Ensure no extra spaces in values
- Click "Save Changes" after editing
- Redeploy if needed

### GitHub Push Failed
```powershell
# Check remotes
git remote -v

# If wrong, remove and re-add
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/mcq-api.git
git push -u origin main
```

### Timeout from Quickbase
- **Cause**: Cold start + MCQ generation time
- **Solution**: Set Pipeline timeout to 180 seconds

### CORS Error
- **Cause**: Quickbase domain not allowed
- **Solution**: Set `ALLOWED_ORIGINS` to your Quickbase domain in Render environment

### MCQ Generation Fails
- Verify PDFs exist in `data/` folders
- Check Render logs for errors
- Test locally first: `python src/mcq_api_service.py`

---

## 🧪 Local Testing

Before deploying, test locally:

```powershell
# Install dependencies
pip install -r requirements.txt

# Run API locally
cd src
python mcq_api_service.py

# In another terminal, test it
cd src
python test_quickbase_integration.py
```

API runs at `http://localhost:8000`

---

## 🔐 Security Notes

### What's Protected
- ✅ `.env` in `.gitignore` - never pushed to GitHub
- ✅ Private GitHub repo option - code stays private
- ✅ Render environment variables - encrypted at rest
- ✅ Optional API key authentication - `X-API-Key` header

### Best Practices
1. **Never** commit `.env` to GitHub
2. Use **strong random keys** for `API_KEY`
3. Set **specific domains** in `ALLOWED_ORIGINS` for production
4. Use **private** GitHub repo if code is proprietary
5. Rotate keys regularly
**View Logs in Real-Time:**
1. Go to Render Dashboard
2. Click your service
3. Click "Logs" tab
4. See all API requests and errors

**Check Service Status:**
- Render Dashboard shows service health
- Use `/health` endpoint for programmatic checks

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid Tier |
|----------|-----------|-----------|
| **Render** | ✅ Free forever | $7/month |
| Azure | ❌ $13/month minimum | $13+/month |
| AWS | ⚠️ Free for 12 months only | $8+/month |
| Heroku | ❌ No free tier anymore | $5/month |

**Winner**: Render.com for this use case! 🏆

---

## 📚 Additional Resources

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **API Documentation**: `https://your-app.onrender.com/docs` (when deployed)
- **Test Script**: Run `python src/test_quickbase_integration.py`
- **Notebook**: Open `Notebook/mcq_generator.ipynb` for step-by-step testing
📋 Quick Command Reference

```powershell
# Navigate to project
cd "C:\Users\abhishek.j.dutta\OneDrive - Accenture\Desktop\Courses\Udemy\rag\WWF"

# First deployment
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/mcq-api.git
git push -u origin main

# Future updates
git add .
git commit -m "Your changes"
git push

# Test locally
cd src
python mcq_api_service.py

# Test deployed API
cd src
python test_quickbase_integration.py
```

---

## ✅ Deployment Checklist

- [ ] Git installed and configured
- [ ] GitHub account created
- [ ] Render account created
- [ ] `.gitignore` verified (excludes .env)
- [ ] Code pushed to GitHub
- [ ] Web Service created in Render
- [ ] GitHub repo connected to Render
- [ ] `GROQ_API_KEY` added in Render Dashboard
- [ ] Optional: `API_KEY` and `ALLOWED_ORIGINS` set
- [ ] Deployment succeeded (check logs)
- [ ] Health check returns "healthy"
- [ ] MCQ generation tested
- [ ] Quickbase Pipeline configured
- [ ] End-to-end test from Quickbase successful

---

## 📚 Documentation Files

- **[README.md](README.md)** (this file) - Complete deployment & usage guide
- **[QUICKBASE.md](QUICKBASE.md)** - Quickbase integration details
- **render.yaml** - Render deployment configuration
- **.env.example** - Environment variable template

---

## 💡 Tips & Best Practices

1. **Always test locally first** before deploying
2. **Use private GitHub repo** for proprietary code
3. **Set strong API_KEY** for production
4. **Monitor Render logs** during initial testing
5. **Set Quickbase timeout to 180s** to account for cold starts
6. **Keep .env local** - verify with `git status`

---

## 🎯 What You've Built

✅ **Secure API** - Environment variables, optional authentication  
✅ **Auto-deploying** - Push to GitHub → Render deploys automatically  
✅ **Free hosting** - Render free tier, forever  
✅ **Production-ready** - HTTPS, logging, error handling  
✅ **Quickbase-ready** - REST API endpoint for pipeline integration  

**Your API URL**: `https://YOUR-APP-NAME.onrender.com`

---

## 🆘 Need Help?

1. **Check Render Logs**: Dashboard → Your Service → Logs
2. **Test Locally**: `python src/mcq_api_service.py`
3. **Run Test Script**: `python src/test_quickbase_integration.py`
4. **Verify Environment**: Check Render Dashboard → Environment
5. **Review QUICKBASE.md**: For integration issues

---

## 🎉 You're All Set!

Your MCQ Generator API is:
- ✅ Deployed on Render (free)
- ✅ Accessible via HTTPS
- ✅ Ready for Quickbase integration
- ✅ Auto-deploying on every push

**Happy coding
**Your Render URL**: `https://YOUR-APP-NAME.onrender.com`

**Ready to deploy!** 🚀
