# WWF Chatbot - Testing Guide (Postman)

## 🎯 Overview

This guide provides step-by-step instructions for testing the WWF Agentic RAG Chatbot via Postman before the UI is ready.

**Backend Features:**
- ✅ Intelligent routing (RAG, Web Search, Hybrid)
- ✅ User context & personalization
- ✅ Chat history persistence (SQLite/PostgreSQL)
- ✅ PDF conversation export
- ✅ Multi-session support

---

## 📋 Prerequisites

### 1. Environment Variables

Create a `.env` file in the `WWF/` directory with:

```ini
# Required for chatbot
GROQ_API_KEY="your_groq_api_key_here"
OPENAI_API_KEY="your_openai_api_key_here"
TAVILY_API_KEY="your_tavily_api_key_here"

# Optional (for local testing, leave empty to use SQLite)
DATABASE_URL=

# Existing variables
QUICKBASE_REALM_HOSTNAME="your_realm.quickbase.com"
QUICKBASE_USER_TOKEN="your_token"
QUICKBASE_TABLE_ID="bvxbt7fyw"
```

### 2. Get API Keys

- **Groq:** https://console.groq.com (already have)
- **OpenAI:** https://platform.openai.com/api-keys
- **Tavily:** https://tavily.com (sign up for free, 1000 searches/month)

### 3. Start Local Server

```bash
cd WWF
python run_server.cmd
```

Server will start at: `http://127.0.0.1:8000`

---

## 🧪 Test Endpoints

### Base URL
```
http://127.0.0.1:8000
```

---

## 1️⃣ Initialize Chat Session

**Endpoint:** `POST /chatbot/session/init`

**Purpose:** Create a new chat session for a user (similar to how Quickbase button will initialize the session)

**Request:**
```json
{
    "user_id": "user_12345",
    "name": "John Doe",
    "education": "Environmental Science",
    "location": "California, USA"
}
```

**Example Postman Setup:**
1. Method: **POST**
2. URL: `http://127.0.0.1:8000/chatbot/session/init`
3. Headers:
   - `Content-Type`: `application/json`
4. Body (raw JSON):
   ```json
   {
       "user_id": "user_12345",
       "name": "John Doe",
       "education": "Environmental Science",
       "location": "California, USA"
   }
   ```

**Expected Response:**
```json
{
    "session_id": "e7f8a9b0-1c2d-3e4f-5a6b-7c8d9e0f1a2b",
    "user_id": "user_12345",
    "message": "Chat session initialized successfully",
    "welcome_message": "Hello John! 👋\n\nI'm your WWF Sustainability Assistant..."
}
```

**Save the `session_id`** - you'll need it for the next requests!

---

## 2️⃣ Send Message (RAG Query)

**Endpoint:** `POST /chatbot/message`

**Purpose:** Ask a question that should be answered from WWF documents

**Request:**
```json
{
    "session_id": "e7f8a9b0-1c2d-3e4f-5a6b-7c8d9e0f1a2b",
    "user_id": "user_12345",
    "message": "What are the key principles of circular economy?"
}
```

**Example Postman Setup:**
1. Method: **POST**
2. URL: `http://127.0.0.1:8000/chatbot/message`
3. Headers:
   - `Content-Type`: `application/json`
4. Body (raw JSON):
   ```json
   {
       "session_id": "e7f8a9b0-1c2d-3e4f-5a6b-7c8d9e0f1a2b",
       "user_id": "user_12345",
       "message": "What are the key principles of circular economy?"
   }
   ```

**Expected Response:**
```json
{
    "message_id": "123",
    "response": "According to WWF documents, circular economy is based on several key principles...",
    "sources": [
        {
            "type": "rag",
            "title": "WWF Document",
            "url": null,
            "excerpt": "Circular economy principles include..."
        }
    ],
    "agent_used": "rag",
    "timestamp": "2026-04-07T20:30:00Z",
    "pdf_url": null
}
```

**Notice:**
- `agent_used: "rag"` - Used RAG agent (ChromaDB)
- `sources` array shows where information came from

---

## 3️⃣ Send Message (Web Search Query)

**Request:**
```json
{
    "session_id": "e7f8a9b0-1c2d-3e4f-5a6b-7c8d9e0f1a2b",
    "user_id": "user_12345",
    "message": "What are the latest WWF initiatives in California in 2026?"
}
```

**Expected Response:**
```json
{
    "message_id": "124",
    "response": "Based on recent information from WWF websites...",
    "sources": [
        {
            "type": "web_search",
            "title": "WWF California Projects 2026",
            "url": "https://www.wwf.org/california/...",
            "excerpt": "In 2026, WWF California launched..."
        }
    ],
    "agent_used": "web_search",
    "timestamp": "2026-04-07T20:31:00Z",
    "pdf_url": null
}
```

**Notice:**
- `agent_used: "web_search"` - Used web search (TavilyAI)
- Keywords "latest" and "2026" triggered web search routing

---

## 4️⃣ Send Message (Hybrid Query)

**Request:**
```json
{
    "session_id": "e7f8a9b0-1c2d-3e4f-5a6b-7c8d9e0f1a2b",
    "user_id": "user_12345",
    "message": "How does circular economy apply to recent California regulations?"
}
```

**Expected Response:**
```json
{
    "message_id": "125",
    "response": "Combining WWF circular economy principles with California's recent regulations...",
    "sources": [
        {
            "type": "rag",
            "title": "WWF Circular Economy Guide",
            "url": null,
            "excerpt": "..."
        },
        {
            "type": "web_search",
            "title": "California Environmental Regulations 2026",
            "url": "https://...",
            "excerpt": "..."
        }
    ],
    "agent_used": "hybrid",
    "timestamp": "2026-04-07T20:32:00Z",
    "pdf_url": null
}
```

**Notice:**
- `agent_used: "hybrid"` - Used BOTH RAG and Web Search
- Sources from both agents combined

---

## 5️⃣ Request PDF Export

**Request:**
```json
{
    "session_id": "e7f8a9b0-1c2d-3e4f-5a6b-7c8d9e0f1a2b",
    "user_id": "user_12345",
    "message": "Can you export this conversation as PDF?"
}
```

**Expected Response:**
```json
{
    "message_id": "126",
    "response": "I'll prepare a PDF export of our conversation for you.\n\n📥 [Download PDF](/chatbot/download/wwf_chat_e7f8a9b0_20260407_203300.pdf)",
    "sources": [],
    "agent_used": "pdf_export",
    "timestamp": "2026-04-07T20:33:00Z",
    "pdf_url": "/chatbot/download/wwf_chat_e7f8a9b0_20260407_203300.pdf"
}
```

**Notice:**
- `agent_used: "pdf_export"` - Detected PDF request
- `pdf_url` contains the download link

---

## 6️⃣ Download PDF

**Endpoint:** `GET /chatbot/download/{filename}`

**Example:**
1. Method: **GET**
2. URL: `http://127.0.0.1:8000/chatbot/download/wwf_chat_e7f8a9b0_20260407_203300.pdf`

**Expected Response:** PDF file download

---

## 7️⃣ Get Chat History

**Endpoint:** `GET /chatbot/session/{session_id}/history`

**Example:**
1. Method: **GET**
2. URL: `http://127.0.0.1:8000/chatbot/session/e7f8a9b0-1c2d-3e4f-5a6b-7c8d9e0f1a2b/history`

**Expected Response:**
```json
{
    "session_id": "e7f8a9b0-1c2d-3e4f-5a6b-7c8d9e0f1a2b",
    "messages": [
        {
            "role": "user",
            "content": "What are the key principles of circular economy?",
            "sources": null,
            "timestamp": "2026-04-07T20:30:00Z"
        },
        {
            "role": "assistant",
            "content": "According to WWF documents...",
            "sources": [...],
            "timestamp": "2026-04-07T20:30:05Z"
        }
    ]
}
```

---

## 8️⃣ Get User's Sessions

**Endpoint:** `GET /chatbot/user/{user_id}/sessions`

**Example:**
1. Method: **GET**
2. URL: `http://127.0.0.1:8000/chatbot/user/user_12345/sessions`

**Expected Response:**
```json
{
    "user_id": "user_12345",
    "sessions": [
        {
            "session_id": "e7f8a9b0-1c2d-3e4f-5a6b-7c8d9e0f1a2b",
            "started_at": "2026-04-07T20:00:00Z",
            "last_activity": "2026-04-07T20:33:00Z",
            "message_count": 10,
            "preview": "Can you export this conversation as PDF?..."
        }
    ]
}
```

---

## 🧪 Test Scenarios

### Scenario 1: New User First Conversation
1. Initialize session with user details
2. Ask a RAG question (e.g., "What is sustainability?")
3. Ask a location-specific question (e.g., "WWF projects in my area")
4. Request PDF export
5. Download PDF

### Scenario 2: Returning User
1. Initialize new session with same `user_id`
2. Get user's previous sessions (should see old session)
3. Start new conversation
4. Get history of current session

### Scenario 3: Test Routing
1. Initialize session
2. Ask document-based question → Should use `rag`
3. Ask current event question → Should use `web_search`
4. Ask combined question → Should use `hybrid`
5. Request PDF → Should use `pdf_export`

---

## 🔍 Testing Tips

1. **Check Logs:** Watch the terminal where server is running to see routing decisions:
   ```
   [Supervisor] Routing to: RAG
   [RAG Agent] Retrieved 5 relevant chunks
   [Response Agent] Generating response...
   ```

2. **Test Different Locations:** Change `location` in init to test personalization:
   - "New York, USA"
   - "London, UK"
   - "Mumbai, India"

3. **Test Education Personalization:** Try different backgrounds:
   - "Environmental Science"
   - "Business Administration"
   - "High School Student"

4. **Test PDF Export Variations:**
   - "export as pdf"
   - "download this chat"
   - "save conversation"
   - "send me pdf"

---

## 🐛 Troubleshooting

### Issue: "TAVILY_API_KEY not found"
**Solution:** Get free API key from https://tavily.com and add to `.env`

### Issue: "OPENAI_API_KEY not found"
**Solution:** Get API key from https://platform.openai.com and add to `.env`

### Issue: "Collection not found"
**Solution:** Ensure ChromaDB vector store exists at `WWF/vector_store/`

### Issue: No sources returned
**Solution:** Check if vector store has data:
```python
import chromadb
client = chromadb.PersistentClient(path="vector_store")
collection = client.get_collection("wwf_knowledge_base")
print(f"Chunks: {collection.count()}")
```

### Issue: PDF not generating
**Solution:** Check if `exports/` folder is writable, verify ReportLab is installed

---

## ✅ Success Checklist

Before deploying to Render, verify:

- [ ] Session initialization works
- [ ] RAG agent retrieves from WWF documents
- [ ] Web search finds recent information
- [ ] Hybrid routing combines both sources
- [ ] PDF export generates downloadable file
- [ ] Chat history persists correctly
- [ ] Multiple sessions work for same user
- [ ] Responses are personalized (mention user's location)

---

## 🚀 Next Steps

Once testing is complete:

1. **Deploy to Render:**
   - Add environment variables (GROQ_API_KEY, OPENAI_API_KEY, TAVILY_API_KEY, DATABASE_URL)
   - Link PostgreSQL database
   - Push to GitHub (auto-deploy)

2. **Build Chat UI:**
   - Next.js + TypeScript + Tailwind
   - Clean, modern design
   - Receives user context from Quickbase button

3. **Quickbase Integration:**
   - Button sends payload: `https://your-chat-ui.com?user_id=X&name=Y&location=Z`
   - UI calls backend API endpoints

---

## 📚 API Documentation

Full API docs available at: `http://127.0.0.1:8000/docs` (Swagger UI)

Interactive testing interface with all endpoints documented!
