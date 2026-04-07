# Local Development Server Guide

## Starting the Server

### Method 1: Using Batch File (Easiest)
Double-click `run_server.cmd` or run from command line:
```cmd
run_server.cmd
```

### Method 2: Using Python
```cmd
cd src
python main.py
```

### Method 3: Using Uvicorn (with auto-reload)
```cmd
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Server URL
- Local: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Testing with Postman

1. Import `Postman_Collection_WWF_API.json`
2. Test health check first
3. Test MCQ generation
4. Test Microlearning generation

## Troubleshooting

Run configuration checker:
```cmd
python check_config.py
```

Common fixes:
- Install dependencies: `pip install -r requirements.txt`
- Create vector store: Run notebook `01_data_ingestion_vector_store.ipynb`
- Check `.env` file has all required variables

See QUICK_START.md for detailed instructions.
