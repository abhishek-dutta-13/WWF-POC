# WWF Learning Content Generator API - Complete Guide

## 📋 Table of Contents
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints Overview](#endpoints-overview)
- [MCQ Generation](#mcq-generation)
- [Microlearning Generation](#microlearning-generation)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)

---

## Base URL

**Production (Render):**
```
https://mcq-generator-api.onrender.com
```
Replace with your actual Render deployment URL.

---

## Authentication

### Optional API Key
If authentication is enabled on the server:
```
X-API-Key: your_api_key_here
```

Check with `/health` endpoint to see if authentication is required.

---

## Endpoints Overview

| Endpoint | Method | Purpose | Time |
|----------|--------|---------|------|
| `/health` | GET | Health check | < 1s |
| `/` | GET | API documentation | < 1s |
| `/generate-mcqs-quickbase` | POST | Generate MCQs + Push to Quickbase | 2-3 min |
| `/generate-microlearning-quickbase` | POST | Generate microlearning + Push to Quickbase | 1-2 min |
| `/generate-microlearning-modules` | POST | Generate microlearning (preview only) | 1-2 min |

---

## MCQ Generation

### Generate MCQs with Quickbase Push

**Endpoint:** `POST /generate-mcqs-quickbase`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "CourseID": "001"
}
```

**Valid Course IDs:**
- `"001"` - Circular Economy and Waste Reduction
- `"002"` - Sustainability Strategy and Compliance
- `"003"` - Sustainable Agriculture and Natural Resources

**Response (200 OK):**
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

**Expected Time:** 2-3 minutes (includes rate limiting)

---

## Microlearning Generation

### Generate Microlearning with Quickbase Push

**Endpoint:** `POST /generate-microlearning-quickbase`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "CourseID": "002"
}
```

**Response (200 OK):**
```json
{
  "microlearning_modules": {
    "categoryName": "Sustainability Strategy And Compliance",
    "courseId": "002",
    "language": "English",
    "chapters": [
      {
        "chapter": "Introduction to Sustainability Strategy",
        "chapterId": "CH-001",
        "microContents": [
          {
            "microContentId": "MC-001",
            "microContent": "Sustainability strategy represents a comprehensive approach to integrating environmental, social, and governance factors into organizational planning...\n\n**Key Components:**\n• Environmental impact assessment\n• Social responsibility initiatives\n• Governance frameworks\n\n**Implementation Steps:**\n1. Conduct materiality assessment\n2. Set measurable targets\n3. Develop action plans..."
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

**Content Details:**
- 4-6 chapters per course
- 3-5 micro-contents per chapter
- 250-400 words per micro-content
- Mix of paragraphs, bullet points, and numbered lists

**Expected Time:** 1-2 minutes

---

### Generate Microlearning (Preview Only)

**Endpoint:** `POST /generate-microlearning-modules`

Same as above but **does NOT push to Quickbase**. Use for testing/preview.

---

## Error Handling

### Common Errors

**Invalid CourseID (400):**
```json
{
  "detail": "Invalid CourseID. Allowed CourseIDs: 001, 002, 003"
}
```

**Unauthorized (401):**
```json
{
  "detail": "Invalid or missing API key. Include X-API-Key header."
}
```

**Server Error (500):**
```json
{
  "detail": "Failed to generate microlearning modules: Collection [wwf_knowledge_base] does not exist"
}
```

---

## Code Examples

### JavaScript (Fetch)

```javascript
async function generateMCQs(courseId) {
  try {
    const response = await fetch('https://mcq-generator-api.onrender.com/generate-mcqs-quickbase', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
        // 'X-API-Key': 'your_key'  // if authentication enabled
      },
      body: JSON.stringify({ CourseID: courseId })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }
    
    const data = await response.json();
    console.log('MCQs generated:', data.mcqs.total_questions);
    console.log('Pushed to Quickbase:', data.quickbase_push.success);
    
    return data;
  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  }
}

// Usage
generateMCQs('001').then(data => {
  // Handle success
}).catch(err => {
  // Handle error
});
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

const API_BASE_URL = 'https://mcq-generator-api.onrender.com';

async function generateMicrolearning(courseId) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/generate-microlearning-quickbase`,
      { CourseID: courseId },
      {
        headers: {
          'Content-Type': 'application/json'
          // 'X-API-Key': 'your_key'  // if needed
        },
        timeout: 180000  // 3 minutes
      }
    );
    
    return response.data;
  } catch (error) {
    if (error.response) {
      console.error('API Error:', error.response.data.detail);
    }
    throw error;
  }
}

// Usage in React
const handleGenerate = async () => {
  setLoading(true);
  try {
    const data = await generateMicrolearning('002');
    setContent(data.microlearning_modules);
    setSuccess(data.quickbase_push.success);
  } catch (err) {
    setError('Failed to generate content');
  } finally {
    setLoading(false);
  }
};
```

### Python (requests)

```python
import requests

API_BASE_URL = "https://mcq-generator-api.onrender.com"

def generate_mcqs(course_id):
    url = f"{API_BASE_URL}/generate-mcqs-quickbase"
    headers = {
        "Content-Type": "application/json"
        # "X-API-Key": "your_key"  # if needed
    }
    payload = {"CourseID": course_id}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=180)
        response.raise_for_status()
        
        data = response.json()
        print(f"Generated {data['mcqs']['total_questions']} MCQs")
        print(f"Pushed to Quickbase: {data['quickbase_push']['success']}")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        raise

# Usage
result = generate_mcqs("001")
```

### cURL

```bash
# Generate MCQs
curl -X POST https://mcq-generator-api.onrender.com/generate-mcqs-quickbase \
  -H "Content-Type: application/json" \
  -d '{"CourseID": "001"}'

# Generate Microlearning
curl -X POST https://mcq-generator-api.onrender.com/generate-microlearning-quickbase \
  -H "Content-Type: application/json" \
  -d '{"CourseID": "002"}'
```

---

## Performance Notes

### Response Times
- **Health Check:** < 1 second
- **MCQ Generation:** 2-3 minutes (intentional rate limiting)
- **Microlearning:** 1-2 minutes (RAG retrieval + LLM generation)
- **First Request:** Add 30-60 seconds (Render cold start on free tier)

### Recommendations for UI
1. **Show loading indicators** with estimated time
2. **Set timeout to 3+ minutes**  
3. **Prevent concurrent requests** - process one course at a time
4. **Handle Render cold starts** - show "Waking up server..." message
5. **Display Quickbase status** - show success/failure of push

---

## Quickbase Integration

### MCQ Table (bvxbt7fyw)

Records pushed: **30 per course**

| Field ID | Field Name | Example |
|----------|------------|---------|
| 19 | Course ID | "001" |
| 8 | Set Number | 1 |
| 10 | Question No | 1 |
| 18 | Question | "What is circular economy?" |
| 11 | Option A | "Linear production" |
| 12 | Option B | "Eliminate waste" |
| 13 | Option C | "Reduce employment" |
| 14 | Option D | "Single-use products" |
| 15 | Correct Answer | "B" |
| 16 | Explanation | "The circular economy aims to..." |

### Microlearning Table (bvxji8seh)

Records pushed: **15-25 per course** (varies)

| Field ID | Field Name | Example |
|----------|------------|---------|
| 12 | Course ID | "001" |
| 20 | Micro Content ID | "MC-001" |
| 8 | Language | "English" |
| 6 | Chapter | "Introduction to..." |
| 7 | Content | "The circular economy represents..." |

---

## Additional Resources

- **Interactive API Docs:** `https://mcq-generator-api.onrender.com/docs`
- **Health Check:** `https://mcq-generator-api.onrender.com/health`
- **ReDoc:** `https://mcq-generator-api.onrender.com/redoc`

---

**Last Updated:** April 7, 2026  
**API Version:** 2.0.0
