"""
Quick Test Script - Verify API Configuration

Run this before starting the server to check if everything is configured correctly.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 80)
print("WWF API Configuration Checker")
print("=" * 80)
print()

# Load environment variables
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print("✅ .env file found and loaded")
else:
    print("❌ .env file not found!")
    print(f"   Expected location: {env_file}")
    sys.exit(1)

print()
print("Checking Environment Variables:")
print("-" * 80)

# Check required environment variables
required_vars = {
    "GROQ_API_KEY": "Groq API for LLM generation",
    "OPENAI_API_KEY": "OpenAI API for embeddings",
    "QUICKBASE_REALM_HOSTNAME": "Quickbase realm hostname",
    "QUICKBASE_USER_TOKEN": "Quickbase authentication token",
    "QUICKBASE_TABLE_ID": "Quickbase MCQ table ID",
    "QUICKBASE_MICROLEARNING_TABLE_ID": "Quickbase microlearning table ID"
}

all_ok = True
for var, description in required_vars.items():
    value = os.getenv(var)
    if value:
        masked_value = value[:10] + "..." if len(value) > 10 else value
        print(f"✅ {var}: {masked_value}")
        print(f"   → {description}")
    else:
        print(f"❌ {var}: NOT SET")
        print(f"   → {description}")
        all_ok = False
    print()

print()
print("Checking Project Structure:")
print("-" * 80)

# Check important files and directories
important_paths = {
    "src/main.py": "Main FastAPI application",
    "src/routers": "API routers directory",
    "src/services": "Business logic services",
    "vector_store": "ChromaDB vector store (created by ingestion notebook)",
    "data/category_file/categories.csv": "Category configuration file",
}

for path_str, description in important_paths.items():
    path = Path(__file__).parent / path_str
    if path.exists():
        print(f"✅ {path_str}")
        print(f"   → {description}")
    else:
        print(f"⚠️  {path_str}: NOT FOUND")
        print(f"   → {description}")
        if "vector_store" in path_str:
            print(f"   → Run Notebook/01_data_ingestion_vector_store.ipynb to create it")
    print()

print()
print("Checking Python Packages:")
print("-" * 80)

required_packages = [
    "fastapi",
    "uvicorn",
    "groq",
    "openai",
    "chromadb",
    "pypdf",
    "langchain",
    "python-dotenv"
]

packages_ok = True
for package in required_packages:
    try:
        __import__(package.replace("-", "_"))
        print(f"✅ {package}")
    except ImportError:
        print(f"❌ {package}: NOT INSTALLED")
        packages_ok = False

if not packages_ok:
    print()
    print("⚠️  Missing packages detected!")
    print("   Run: pip install -r requirements.txt")

print()
print("=" * 80)
print("Configuration Summary")
print("=" * 80)

if all_ok and packages_ok:
    print("✅ All checks passed! You're ready to start the server.")
    print()
    print("To start the server:")
    print("  1. Double-click run_server.cmd")
    print("  2. Or run: cd src && python main.py")
    print()
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
else:
    print("⚠️  Some issues detected. Please fix them before starting the server.")
    print()
    if not all_ok:
        print("Missing environment variables:")
        print("  → Check your .env file and add missing variables")
    if not packages_ok:
        print("Missing Python packages:")
        print("  → Run: pip install -r requirements.txt")

print()
print("=" * 80)
