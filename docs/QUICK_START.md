# 🚀 Quick Start - Local Server Testing

## Step-by-Step Guide

### 1️⃣ Check Configuration
Run the configuration checker first:
```cmd
python check_config.py
```

This will verify:
- ✅ Environment variables (.env)
- ✅ Python packages installed
- ✅ Project structure
- ✅ Vector store exists

### 2️⃣ Start the Server

**Option A: Easy Start (Recommended)**
```cmd
run_server.cmd
```

**Option B: Manual Start**
```cmd
cd src
python main.py
```

Server will start on: **http://localhost:8000**

### 3️⃣ Test with Postman

1. **Import Collection**
   - Open Postman
   - Click "Import"
   - Select: `Postman_Collection_WWF_API.json`

2. **Test Health Check**
   ```
   GET http://localhost:8000/health
   ```

3. **Test MCQ Generation**
   ```
   POST http://localhost:8000/generate-mcqs-quickbase
   Body: {"CourseID": "001"}
   ```

4. **Test Microlearning Generation**
   ```
   POST http://localhost:8000/generate-microlearning-quickbase
   Body: {"CourseID": "001"}
   ```

## 📁 Files Created

| File | Purpose |
|------|---------|
| `run_server.cmd` | Windows batch file to start server easily |
| `check_config.py` | Verify configuration before starting |
| `Postman_Collection_WWF_API.json` | Pre-configured Postman requests |
| `LOCAL_SERVER_GUIDE.md` | Detailed server documentation |

## 🎯 Available Endpoints

Once server is running:

- **API Info**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Main Endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate-mcqs-quickbase` | POST | Generate MCQs + Push to Quickbase |
| `/generate-microlearning-quickbase` | POST | Generate Microlearning + Push to Quickbase |
| `/generate-microlearning-modules` | POST | Generate Microlearning (No Push) |

## 📋 Request Format

All POST endpoints use the same format:
```json
{
  "CourseID": "001"
}
```

**Course IDs:**
- `001` - Circular Economy and Waste Reduction
- `002` - Sustainability Strategy and Compliance  
- `003` - Sustainable Agriculture and Natural Resources

## 🐛 Common Issues

**Server won't start?**
- Run `python check_config.py` to diagnose
- Check `.env` file has all required variables
- Install dependencies: `pip install -r requirements.txt`

**Vector store not found?**
- Run `Notebook/01_data_ingestion_vector_store.ipynb` first

**Quickbase push fails?**
- Verify `QUICKBASE_USER_TOKEN` in `.env`
- Check `QUICKBASE_REALM_HOSTNAME` is correct

## 📖 Full Documentation

See `LOCAL_SERVER_GUIDE.md` for detailed instructions.

---

**Ready to Deploy?**

Once local testing is complete:
1. Test all endpoints in Postman ✅
2. Verify Quickbase integration ✅
3. Check logs for errors ✅
4. Review response formats ✅

Then proceed to deployment!
