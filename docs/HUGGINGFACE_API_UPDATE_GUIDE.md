# 🔄 Notebook Update Guide - HuggingFace API for Embeddings

## Overview
The notebooks need to be updated to use **HuggingFace Inference API** for embeddings instead of loading models locally. This makes everything API-based.

---

## ✅ What's Already Done

1. ✅ **microlearning_generator.py** - Updated with `HuggingFaceEmbeddings` class
2. ✅ **requirements.txt** - Removed `sentence-transformers`, added comments about HuggingFace API
3. ✅ **.env** - Contains `HUGGINGFACE_API_TOKEN`

---

## 📝 Manual Updates Needed

### **Notebook 1: `01_data_ingestion_vector_store.ipynb`**

#### Cell 2: Imports (Update)
**Find:**
```python
from sentence_transformers import SentenceTransformer
```

**Replace with:**
```python
import requests
from dotenv import load_dotenv

# Load environment variables
env_path = Path(r"C:\Users\abhishek.j.dutta\OneDrive - Accenture\Desktop\Courses\Udemy\rag\WWF\.env")
load_dotenv(env_path)
```

#### Cell 4: Configuration (Update)
**Find:**
```python
# Embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

**Replace with:**
```python
# HuggingFace Embedding Model (via Inference API)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

if not HUGGINGFACE_API_TOKEN:
    raise ValueError("❌ HUGGINGFACE_API_TOKEN not found in environment variables")

print(f"🤖 Embedding Model (via HuggingFace API): {EMBEDDING_MODEL}")
```

#### Cell 5: Initialize Embedding Model (REPLACE ENTIRE CELL)
**Find:**
```python
print("🔄 Loading embedding model...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL)
print(f"✅ Embedding model loaded: {EMBEDDING_MODEL}")
print(f"   Embedding dimension: {embedding_model.get_sentence_embedding_dimension()}")
```

**Replace with:**
```python
# HuggingFace Embeddings Helper Class
class HuggingFaceEmbeddings:
    """Generate embeddings using HuggingFace Inference API."""
    
    def __init__(self, model_name: str, api_token: str):
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_name}"
        self.headers = {"Authorization": f"Bearer {api_token}"}
    
    def encode(self, texts: List[str], show_progress_bar: bool = False) -> List[List[float]]:
        """Generate embeddings via HuggingFace API."""
        if isinstance(texts, str):
            texts = [texts]
        
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json={"inputs": texts, "options": {"wait_for_model": True}}
        )
        response.raise_for_status()
        return response.json()
    
    def get_sentence_embedding_dimension(self) -> int:
        """Return embedding dimension (384 for all-MiniLM-L6-v2)."""
        return 384

print("🔄 Initializing HuggingFace embeddings via API...")
embedding_model = HuggingFaceEmbeddings(EMBEDDING_MODEL, HUGGINGFACE_API_TOKEN)
print(f"✅ HuggingFace API embeddings initialized: {EMBEDDING_MODEL}")
print(f"   Embedding dimension: {embedding_model.get_sentence_embedding_dimension()}")
```

#### Cell 10: Generate Embeddings (Update batch processing)
**Find:**
```python
batch_size = 100  # Process in batches for efficiency
```

**Replace with:**
```python
batch_size = 50  # Smaller batches for API calls to avoid timeouts
```

**Also add at the top of the cell:**
```python
print("🌐 Using HuggingFace Inference API - no local model loading required!")
```

**And add after embedding generation:**
```python
    try:
        embeddings = embedding_model.encode(texts, show_progress_bar=False)
        if isinstance(embeddings, list):
            embeddings_list = embeddings
        else:
            embeddings_list = embeddings.tolist()
    except Exception as e:
        print(f"   ⚠️  Error getting embeddings for batch {batch_num}: {e}")
        print(f"   ⏳ Retrying after 5 seconds...")
        time.sleep(5)
        embeddings = embedding_model.encode(texts, show_progress_bar=False)
        if isinstance(embeddings, list):
            embeddings_list = embeddings
        else:
            embeddings_list = embeddings.tolist()
```

---

### **Notebook 2: `02_test_microlearning_generation.ipynb`**

#### Cell 2: Imports (Update)
**Find:**
```python
from sentence_transformers import SentenceTransformer
```

**Replace with:**
```python
import requests
```

#### Cell 4: Configuration (Update)
**Find:**
```python
# Embedding model (must match ingestion)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

**Replace with:**
```python
# HuggingFace API Token
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
if not HUGGINGFACE_API_TOKEN:
    raise ValueError("❌ HUGGINGFACE_API_TOKEN not found in .env file")

# Embedding model (must match ingestion)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

print(f"🤖 Embedding Model (via HuggingFace API): {EMBEDDING_MODEL}")
```

#### Cell 5: Initialize Models (Update)
**Find:**
```python
print("🔄 Loading embedding model...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL)
print(f"✅ Embedding model loaded")
```

**Replace with:**
```python
# HuggingFace Embeddings Helper Class
class HuggingFaceEmbeddings:
    """Generate embeddings using HuggingFace Inference API."""
    
    def __init__(self, model_name: str, api_token: str):
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_name}"
        self.headers = {"Authorization": f"Bearer {api_token}"}
    
    def encode(self, texts: List[str], show_progress_bar: bool = False) -> List[List[float]]:
        """Generate embeddings via HuggingFace API."""
        if isinstance(texts, str):
            texts = [texts]
        
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json={"inputs": texts, "options": {"wait_for_model": True}}
        )
        response.raise_for_status()
        return response.json()

print("🔄 Initializing HuggingFace embeddings via API...")
embedding_model = HuggingFaceEmbeddings(EMBEDDING_MODEL, HUGGINGFACE_API_TOKEN)
print(f"✅ HuggingFace API embeddings initialized")
```

---

## 🎯 Alternative: Use the Updated Module Directly

**Instead of updating the notebooks**, you can simply use the updated `microlearning_generator.py` module which already has HuggingFace API support.

### Quick Test Script

Create a new file `test_microlearning_api.py`:

```python
from src.microlearning_generator import create_generator_from_env
import json

# Initialize generator (will use HuggingFace API)
generator = create_generator_from_env()

# Test all categories
categories = [
    "circular_economy_and_waste_reduction",
    "sustainability_strategy_and_compliance",
    "sustainable_agriculture_and_natural_resources"
]

for category in categories:
    print(f"\n{'='*80}")
    print(f"Generating micro-learning for: {category}")
    print(f"{'='*80}")
    
    modules = generator.generate_microlearning_modules(category)
    
    # Save to file
    with open(f"microlearning_{category}.json", 'w', encoding='utf-8') as f:
        json.dump(modules, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to: microlearning_{category}.json")
    
    # Validate
    validation = generator.validate_modules(modules)
    print(f"\n📊 Validation: {validation['valid']}")
    print(f"   Chapters: {validation['statistics']['chapter_count']}")
    print(f"   Micro-contents: {validation['statistics']['total_micro_contents']}")
```

Run it:
```powershell
python test_microlearning_api.py
```

---

## ✅ Benefits of HuggingFace API Implementation

1. **✅ No local model loading** - Faster startup times
2. **✅ Less memory usage** - No 1-2GB model in RAM
3. **✅ Always up-to-date** - HuggingFace manages the models
4. **✅ No GPU needed** - Everything runs via API
5. **✅ Consistent with Groq LLM** - All via API calls
6. **✅ Smaller deployment size** - No model files to upload
7. **✅ Free tier available** - HuggingFace Inference API is free

---

## 🔧 Verification

After updating, verify it works:

### 1. Test HuggingFace API directly:
```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HUGGINGFACE_API_TOKEN")

response = requests.post(
    "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2",
    headers={"Authorization": f"Bearer {token}"},
    json={"inputs": ["Hello world"], "options": {"wait_for_model": True}}
)
print(f"Status: {response.status_code}")
print(f"Embedding dimension: {len(response.json()[0])}")
```

Expected output:
```
Status: 200
Embedding dimension: 384
```

### 2. Test the module:
```python
from src.microlearning_generator import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("HUGGINGFACE_API_TOKEN")

embedder = HuggingFaceEmbeddings(
    "sentence-transformers/all-MiniLM-L6-v2",
    token
)

embeddings = embedder.encode(["Test text"])
print(f"Embedding dimension: {len(embeddings[0])}")
```

---

## 📚 Documentation Updates

The following files have been updated:
- ✅ `src/microlearning_generator.py` - Uses `HuggingFaceEmbeddings` class
- ✅ `requirements.txt` - Removed `sentence-transformers`
- ⚠️ Notebooks need manual update (see above) OR use the Python module directly

---

## 🚀 Quick Start (Recommended Approach)

**Don't update notebooks manually** - Instead:

1. **Create vector store using existing notebook** (one-time)
   - Run `01_data_ingestion_vector_store.ipynb` with updates OR
   - Use the test script approach above

2. **Use API directly** for testing and production
   ```powershell
   # Start API
   cd src
   uvicorn mcq_api_service:app --reload
   
   # Test endpoint
   curl --location "http://localhost:8000/generate-microlearning-quickbase" \
     --header "Content-Type: application/json" \
     --data '{"category": "circular_economy_and_waste_reduction"}'
   ```

3. **The API handles everything via HuggingFace automatically!**

---

## ❓ Troubleshooting

### Error: "Authorization token is required"
➡️ Check that `HUGGINGFACE_API_TOKEN` is in your `.env` file

### Error: "Rate limit exceeded"
➡️ Wait a few seconds between requests, or upgrade to HuggingFace Pro

### Error: "Model is loading"
➡️ First call may take 10-20 seconds while HuggingFace loads the model. Use `{"wait_for_model": True}` option (already included in the code)

---

**Ready to use!** 🎉

The microlearning API endpoint is now fully API-based with HuggingFace for embeddings and Groq for LLM.
