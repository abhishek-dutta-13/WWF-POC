# Micro-Learning Module Generator - RAG-based Implementation

## Overview

The micro-learning module generator creates comprehensive, structured educational content from WWF sustainability documents using a RAG (Retrieval-Augmented Generation) approach.

### Key Features

✅ **RAG-powered Content Retrieval** - Retrieves relevant content from ChromaDB vector store  
✅ **Extensive Educational Content** - Each micro-content is 150-300 words with detailed explanations  
✅ **Multi-chapter Structure** - 4-6 chapters per category with 3-5 micro-contents each  
✅ **Category-based Filtering** - Metadata filtering ensures content relevance  
✅ **Production-ready API** - FastAPI endpoint with authentication and validation  
✅ **Quickbase Integration Ready** - JSON format matches Quickbase requirements  

---

## Architecture

### RAG Pipeline

```
User Request
    ↓
Category Validation
    ↓
ChromaDB Query (Metadata Filter: category)
    ↓
Retrieve Top 20 Relevant Chunks
    ↓
Groq LLM (Meta Llama 4 Scout)
    ↓
Structured Micro-Learning JSON
    ↓
Quality Validation
    ↓
Return to Client
```

### Components

1. **Vector Store** (`vector_store/`)
   - ChromaDB persistent storage
   - Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
   - Metadata: category, source_file, chunk_index, doc_type

2. **Ingestion Pipeline** (`Notebook/01_data_ingestion_vector_store.ipynb`)
   - PDF text extraction
   - Intelligent chunking (1000 chars, 800 overlap)
   - Embedding generation
   - Vector store population

3. **Generator Module** (`src/microlearning_generator.py`)
   - Content retrieval from ChromaDB
   - LLM prompt engineering
   - JSON response formatting
   - Quality validation

4. **API Endpoint** (`/generate-microlearning-quickbase`)
   - FastAPI route in `mcq_api_service.py`
   - Authentication support
   - Error handling
   - Response validation

---

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Vector Store

Run the data ingestion notebook to create the vector store:

```bash
# Open Jupyter and run:
Notebook/01_data_ingestion_vector_store.ipynb
```

This will:
- Process all PDFs in `data/{category}/` folders
- Create embeddings with 800-character overlap
- Store in `vector_store/` directory
- Generate metadata for filtering

**Expected Output:**
```
✅ VECTOR STORE CREATION COMPLETE!
💾 Total chunks stored: 500+ (varies by content)
📁 Vector store location: C:\...\WWF\vector_store
🎯 Collection name: wwf_knowledge_base
```

### 3. Test Generation (Optional)

Run the testing notebook to verify micro-module generation:

```bash
# Open Jupyter and run:
Notebook/02_test_microlearning_generation.ipynb
```

This will:
- Test content retrieval for each category
- Generate sample micro-learning modules
- Validate content quality (word count, structure)
- Export JSON examples

---

## API Usage

### Endpoint

```
POST /generate-microlearning-quickbase
```

### Request Format

```json
{
  "category": "circular_economy_and_waste_reduction"
}
```

### Response Format

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
          "microContent": "A comprehensive 150-300 word explanation covering the fundamentals of circular economy, including specific examples of how businesses are transitioning from linear 'take-make-dispose' models to regenerative systems. The circular economy represents a systemic shift towards designing out waste and pollution, keeping products and materials in use, and regenerating natural systems..."
        },
        {
          "microContentId": "MC-002",
          "microContent": "Another detailed micro-content..."
        }
      ]
    },
    {
      "chapter": "Waste Reduction Strategies",
      "microContents": [
        {
          "microContentId": "MC-003",
          "microContent": "Detailed explanation of waste reduction approaches..."
        }
      ]
    }
  ]
}
```

### cURL Example

```bash
curl --location "http://localhost:8000/generate-microlearning-quickbase" \
  --header "Content-Type: application/json" \
  --header "X-API-Key: your_api_key_here" \
  --data '{
    "category": "circular_economy_and_waste_reduction"
  }'
```

### Python Example

```python
import requests

url = "http://localhost:8000/generate-microlearning-quickbase"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your_api_key_here"  # Optional, if configured
}
data = {
    "category": "sustainable_agriculture_and_natural_resources"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

print(f"Generated {len(result['chapters'])} chapters")
for chapter in result['chapters']:
    print(f"- {chapter['chapter']}: {len(chapter['microContents'])} micro-contents")
```

---

## Available Categories

The system supports the following categories (loaded from `data/category_file/categories.csv`):

1. `circular_economy_and_waste_reduction`
2. `sustainability_strategy_and_compliance`
3. `sustainable_agriculture_and_natural_resources`

To add new categories:
1. Add PDFs to `data/{new_category}/`
2. Add category to `data/category_file/categories.csv`
3. Re-run the data ingestion notebook

---

## Content Quality Guidelines

Each micro-content is designed to be:

### ✅ Extensive (150-300 words)
- NOT one-liners or brief summaries
- Comprehensive explanations with context
- Multiple sentences forming complete paragraphs

### ✅ Educational
- Clear definitions and concepts
- Specific examples and case studies
- Relevant data and statistics
- Practical applications

### ✅ Professional
- Accessible language for diverse audiences
- Proper terminology
- Well-structured flow
- Engaging and informative

### Example Quality Check

**❌ BAD (too brief):**
```
"Circular economy reduces waste by reusing materials."
```

**✅ GOOD (extensive and educational):**
```
"The circular economy represents a fundamental shift from the traditional linear 'take-make-dispose' model to a regenerative system that designs out waste and pollution. In practice, this means businesses are reimagining product lifecycles to keep materials in use for as long as possible through strategies like design for durability, repair services, refurbishment programs, and material recycling. For example, companies like Patagonia have implemented take-back programs where customers can return worn clothing for repair or recycling, demonstrating how circular principles can be applied in the fashion industry. This approach not only reduces environmental impact but also creates new business opportunities in service-based models and material recovery..."
```

---

## Performance and Scalability

### Response Times
- **Cold Start** (first request): 8-15 seconds
- **Warm Requests**: 5-10 seconds
- **Vector Retrieval**: ~1 second
- **LLM Generation**: 4-9 seconds

### Resource Usage
- **Vector Store Size**: 50-200 MB (depends on document count)
- **Memory**: ~2-4 GB (includes embedding model + vector DB)
- **ChromaDB**: Persistent file-based storage

### Optimization Tips

1. **Warm-up on Startup**
   - The first request initializes the vector store and embedding model
   - Consider preloading in production

2. **Caching**
   - Results can be cached by category if content doesn't change frequently
   - Implement Redis or similar for production

3. **Parallel Processing**
   - Multiple categories can be processed in parallel
   - Use async/await for concurrent requests

---

## Deployment

### Local Development

```bash
# Start the API server
cd src
uvicorn mcq_api_service:app --reload --port 8000
```

### Production (Render)

The service is designed to deploy seamlessly to Render alongside the MCQ generator.

**Key Considerations:**

1. **Vector Store Persistence**
   - Upload `vector_store/` directory to your deployment
   - Use Render disk storage or mount a persistent volume

2. **Environment Variables**
   ```
   GROQ_API_KEY=your_groq_api_key
   VECTOR_STORE_PATH=/opt/render/project/src/vector_store
   ```

3. **Cold Start Time**
   - First request may take 15-20 seconds (model loading)
   - Set Render timeout to 60+ seconds

4. **Memory Requirements**
   - Recommend: 2-4 GB RAM plan
   - Vector store + embedding model + LLM

---

## Troubleshooting

### Issue: "No content found for category"

**Cause**: Vector store not populated or category missing  
**Solution**: 
1. Verify vector store exists at correct path
2. Re-run data ingestion notebook
3. Check category name matches exactly

### Issue: "Failed to initialize microlearning generator"

**Cause**: Missing dependencies or vector store path incorrect  
**Solution**:
1. Install all requirements: `pip install -r requirements.txt`
2. Check VECTOR_STORE_PATH environment variable
3. Verify vector store directory exists

### Issue: Content quality too brief (< 100 words)

**Cause**: LLM not following prompt instructions  
**Solution**:
1. Check validation warnings in logs
2. Adjust prompt in `microlearning_generator.py`
3. Increase `temperature` parameter for more variation
4. Review source PDFs for sufficient content

### Issue: Slow response times

**Cause**: Cold start or large retrieval  
**Solution**:
1. Reduce `top_k_chunks` from 20 to 15
2. Reduce `max_chunks_for_llm` from 15 to 10
3. Implement response caching
4. Use faster embedding model

---

## Integration with Quickbase

The JSON response format is designed for direct integration with Quickbase:

1. **Category Name** → Text field
2. **Course ID** → Unique identifier
3. **Chapters** → Related table or multi-line text
4. **Micro-contents** → Child records with ID and content

### Sample Quickbase Workflow

```javascript
// Quickbase webhook or automation
fetch('https://your-api.onrender.com/generate-microlearning-quickbase', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your_api_key'
  },
  body: JSON.stringify({
    category: 'circular_economy_and_waste_reduction'
  })
})
.then(response => response.json())
.then(data => {
  // Insert chapters and micro-contents into Quickbase
  data.chapters.forEach(chapter => {
    // Create chapter record
    // Create micro-content child records
  });
});
```

---

## Future Enhancements

### Planned Features

- [ ] Multi-language support (Spanish, French, etc.)
- [ ] Difficulty levels (Beginner, Intermediate, Advanced)
- [ ] Learning objectives per chapter
- [ ] Quiz question integration with micro-contents
- [ ] Progress tracking metadata
- [ ] Content versioning and updates
- [ ] Cross-category topic discovery
- [ ] Semantic search for specific topics

### Customization Options

Users can customize:
- Number of chapters (default: 4-6)
- Micro-contents per chapter (default: 3-5)
- Word count per micro-content (default: 150-300)
- Tone and style (formal, conversational, etc.)
- Retrieval parameters (top-k, similarity threshold)

---

## Technical Details

### Vector Store Schema

```python
{
  "id": "category_filename_chunkindex",
  "embedding": [0.123, -0.456, ...],  # 384 dimensions
  "document": "chunk text...",
  "metadata": {
    "category": "circular_economy_and_waste_reduction",
    "source_file": "cewr_1.pdf",
    "chunk_index": 1,
    "total_chunks": 50,
    "doc_type": "pdf",
    "ingestion_date": "2026-04-06T10:30:00"
  }
}
```

### LLM Prompt Structure

The prompt engineering ensures:
1. **Context provision** - Source material excerpts
2. **Structure requirements** - JSON schema specification
3. **Quality guidelines** - Word counts, detail level
4. **Educational focus** - Learning outcomes emphasis

### Embedding Model

- **Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Advantages**: Fast, lightweight, good quality
- **Alternative**: `all-mpnet-base-v2` (higher quality, slower)

---

## Support and Documentation

- **API Docs**: `http://localhost:8000/docs` (interactive Swagger UI)
- **Issues**: Contact development team
- **Source**: `src/microlearning_generator.py`
- **Tests**: `Notebook/02_test_microlearning_generation.ipynb`

---

**Last Updated**: April 6, 2026  
**Version**: 1.0.0  
**Author**: AI-Powered Content Generation Team
