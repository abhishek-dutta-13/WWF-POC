# WWF Agentic RAG Chatbot - Implementation Approach

## 📋 Executive Summary

Building a personalized, region-aware sustainability chatbot that intelligently routes between:
- **Vector DB (RAG)** - For WWF document-based knowledge
- **Web Search** - For real-time, region-specific information
- **Hybrid** - For comprehensive answers

---

## 🎯 Requirements Analysis

### Functional Requirements
1. ✅ Accept user context (name, education, location, user_id)
2. ✅ Intelligent routing between RAG and web search
3. ✅ Region-aware, personalized responses
4. ✅ Chat history persistence per user
5. ✅ PDF export of conversations
6. ✅ Anti-hallucination safeguards
7. ✅ Production-ready TypeScript UI
8. ✅ WWF-branded interface

### Technical Requirements
- **Embeddings:** OpenAI (text-embedding-3-small)
- **LLM:** Groq (llama-3.3-70b-versatile)
- **Vector DB:** ChromaDB (existing)
- **Web Search:** TavilyAI (best for agentic workflows)
- **Agent Framework:** LangGraph (recommended)
- **Backend:** FastAPI
- **Frontend:** TypeScript (React/Next.js recommended)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         USER REQUEST                         │
│  {user_id, name, location, education, query}                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   AGENT SUPERVISOR                           │
│  (Analyzes query + user context)                            │
│  Decision: RAG | Web Search | Hybrid                        │
└─────────────┬───────────────────┬───────────────────────────┘
              │                   │
       ┌──────▼──────┐     ┌─────▼──────┐
       │   RAG Agent  │     │ Web Search │
       │             │     │   Agent    │
       │ ChromaDB    │     │ TavilyAI   │
       │ + OpenAI    │     │ (WWF focus)│
       └──────┬──────┘     └─────┬──────┘
              │                   │
              └────────┬──────────┘
                       │
              ┌────────▼────────┐
              │  Response Agent │
              │  (Synthesizes)  │
              │  Groq LLM       │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │ Chat History DB │
              │ (PostgreSQL/    │
              │  SQLite)        │
              └─────────────────┘
```

---

## 🔀 Agent Routing Strategy (LangGraph)

### Agent Types

#### 1. **Supervisor Agent**
**Role:** Query analysis and routing

**Decision Logic:**
```python
def route_query(query: str, user_context: dict) -> str:
    """
    Routes to appropriate agent based on query intent
    """
    # Check for:
    # - Document-based questions → RAG Agent
    # - Current events/news → Web Search Agent
    # - Region-specific queries → Web Search Agent (with location filter)
    # - General sustainability → Hybrid (both agents)
    # - WWF programs/reports → RAG Agent
    # - Local regulations → Web Search Agent
    # - PDF export request → PDF Export Tool
    
    return "rag" | "web_search" | "hybrid" | "pdf_export"
```

**Routing Rules:**
- **RAG Agent** if query contains:
  - "according to WWF documents"
  - "WWF report says"
  - "circular economy principles"
  - "sustainability strategy"
  - General concepts covered in PDFs

- **Web Search Agent** if query contains:
  - "latest", "current", "recent", "news"
  - "in [location]", location-specific terms
  - "regulations in", "laws in"
  - "WWF project in [location]"

- **Hybrid** if query needs both:
  - "How does [concept] apply in [location]?"
  - "Latest developments in [WWF topic]"

- **PDF Export Tool** if query contains:
  - "export", "download", "save as PDF"
  - "get a copy", "send me the chat"
  - "PDF of this conversation"

#### 2. **RAG Agent**
**Role:** Retrieve from vector DB

**Process:**
1. Embed query using OpenAI
2. Retrieve top-k chunks from ChromaDB
3. Filter by relevance score (>0.7)
4. Return context to Response Agent

**Implementation:**
```python
class RAGAgent:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path="vector_store")
        self.collection = self.chroma_client.get_collection("wwf_knowledge_base")
        self.embedding_function = OpenAIEmbeddingFunction()
    
    def retrieve(self, query: str, user_location: str, top_k: int = 10):
        # Enhance query with location context
        enhanced_query = f"{query} in context of {user_location}"
        
        # Retrieve relevant chunks
        results = self.collection.query(
            query_texts=[enhanced_query],
            n_results=top_k
        )
        
        return results
```

#### 3. **Web Search Agent**
**Role:** Real-time web search focused on WWF domains

**Implementation:**
```python
from langchain_community.tools.tavily_search import TavilySearchResults

class WebSearchAgent:
    def __init__(self):
        self.search_tool = TavilySearchResults(
            max_results=5,
            search_depth="advanced",
            include_domains=[
                "wwf.org",
                "worldwildlife.org",
                "panda.org",
                "wwf.org.uk",
                "wwf.de",
                # Regional WWF sites
            ]
        )
    
    def search(self, query: str, user_location: str):
        # Enhance query with location
        location_query = f"{query} {user_location} site:wwf.org OR site:worldwildlife.org"
        
        results = self.search_tool.invoke(location_query)
        return results
```

**Why TavilyAI?**
- ✅ Built for AI agents
- ✅ Returns clean, summarized results
- ✅ Domain filtering support
- ✅ Fast and reliable
- ✅ Better than Serper/Google for agent workflows

#### 4. **Response Agent**
**Role:** Generate personalized answer

**Prompt Template:**
```python
RESPONSE_PROMPT = """
You are a WWF Sustainability Expert Assistant helping {user_name}, who has a background in {education} and is located in {location}.

IMPORTANT GUIDELINES:
1. NEVER hallucinate or make up information
2. If information is from documents, cite "According to WWF documents..."
3. If information is from web search, cite the source
4. If you don't know, say "I don't have verified information on this"
5. Personalize answers based on user's location ({location})
6. Consider regional environmental context
7. Provide actionable, region-specific advice when possible

CONTEXT FROM VECTOR DB:
{rag_context}

CONTEXT FROM WEB SEARCH:
{web_context}

USER QUESTION:
{query}

Provide a comprehensive, accurate, and personalized answer. If relevant, mention region-specific initiatives or regulations for {location}.
"""
```

#### 5. **PDF Export Tool**
**Role:** Generate PDF when user requests

**Trigger Detection:**
```python
def is_pdf_export_request(query: str) -> bool:
    """Detect if user wants to export chat as PDF"""
    export_keywords = [
        "export", "download", "save as pdf", "pdf",
        "get a copy", "send me", "email this",
        "save this conversation", "save chat"
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in export_keywords)
```

**Response Flow:**
1. Detect PDF export request
2. Generate PDF from current session
3. Return download link
4. Respond: "I've generated a PDF of our conversation. You can download it here: [link]"

**Implementation:**
```python
class ResponseAgent:
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    def generate_response(
        self,
        query: str,
        user_context: dict,
        rag_context: str,
        web_context: str
    ):
        prompt = RESPONSE_PROMPT.format(
            user_name=user_context['name'],
            education=user_context['education'],
            location=user_context['location'],
            rag_context=rag_context,
            web_context=web_context,
            query=query
        )
        
        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a WWF Sustainability Expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower for factual accuracy
            max_tokens=1500
        )
        
        return response.choices[0].message.content
```

---

## 🗄️ Chat History & Session Management

### Database Schema

**Option 1: SQLite (Simple, file-based)**
```sql
-- Users table
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    education TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat sessions
CREATE TABLE chat_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Chat messages
CREATE TABLE chat_messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    user_id TEXT,
    role TEXT CHECK(role IN ('user', 'assistant')),
    content TEXT,
    metadata JSON,  -- stores source (rag/web), citations, etc.
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);

-- Create indexes for faster queries
CREATE INDEX idx_user_messages ON chat_messages(user_id, timestamp);
CREATE INDEX idx_session_messages ON chat_messages(session_id, timestamp);
```

**Option 2: PostgreSQL (Production-grade, scalable)**
Same schema but with better JSON support and performance for high traffic.

**Recommendation:** Start with SQLite, migrate to PostgreSQL if needed.

---

## 📡 API Endpoints

### Backend API Structure

```
src/
├── chatbot/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── supervisor.py      # Routing logic
│   │   ├── rag_agent.py       # Vector DB retrieval
│   │   ├── web_search_agent.py # TavilyAI search
│   │   ├── response_agent.py  # LLM response generation
│   │   └── graph.py           # LangGraph workflow
│   ├── models.py              # Pydantic models
│   ├── database.py            # Chat history DB
│   ├── pdf_generator.py       # PDF export
│   └── router.py              # FastAPI routes
```

### API Endpoints

#### 1. Initialize Chat Session
```python
POST /chatbot/session/init
Request:
{
    "user_id": "user_12345",
    "name": "John Doe",
    "education": "Environmental Science",
    "location": "California, USA"
}

Response:
{
    "session_id": "session_abc123",
    "user_id": "user_12345",
    "message": "Chat session initialized",
    "welcome_message": "Hello John! I'm here to help with sustainability questions specific to California."
}
```

#### 2. Send Message
```python
POST /chatbot/message
Request:
{
    "session_id": "session_abc123",
    "user_id": "user_12345",
    "message": "What are the latest circular economy initiatives in California?"
}

Response:
{
    "message_id": "msg_789",
    "response": "Based on recent information from WWF and California government sources...",
    "sources": [
        {
            "type": "web_search",
            "title": "California Circular Economy Initiative",
            "url": "https://wwf.org/california-circular-economy",
            "excerpt": "..."
        }
    ],
    "agent_used": "hybrid",  # rag | web_search | hybrid
    "timestamp": "2026-04-07T20:30:00Z"
}
```

#### 3. Get Chat History
```python
GET /chatbot/session/{session_id}/history
Response:
{
    "session_id": "session_abc123",
    "messages": [
        {
            "role": "user",
            "content": "What are circular economy principles?",
            "timestamp": "2026-04-07T20:15:00Z"
        },
        {
            "role": "assistant",
            "content": "According to WWF documents...",
            "sources": [...],
            "timestamp": "2026-04-07T20:15:05Z"
        }
    ]Download PDF (Internal)
```python
GET /chatbot/download/{session_id}.pdf
Response: PDF file

Note: This endpoint is called internally by the chatbot when user requests PDF export in conversation.
Not exposed as a standalone feature - only triggered by conversational intent.esponse:
{
    "user_id": "user_12345",
    "sessions": [
        {
            "session_id": "session_abc123",
            "started_at": "2026-04-07T20:00:00Z",
            "last_activity": "2026-04-07T20:30:00Z",
            "message_count": 12,
            "preview": "Latest message preview..."
        }
    ]
}
```

#### 5. Export to PDF
```python
POST /chatbot/session/{session_id}/export
Response:
{
    "pdf_url": "/downloads/chat_session_abc123.pdf",
    "download_link": "https://api.com/chatbot/download/session_abc123.pdf"
}
```

---

## 🎨 Frontend UI Structure (TypeScript)

### Recommended Tech Stack

**Framework:** Next.js 14 (App Router) with TypeScript
- ✅ Server-side rendering for SEO
- ✅ Built-in API routes
- ✅ TypeScript native
- ✅ Production-ready

**UI Library:** Tailwind CSS + shadcn/ui
- ✅ Clean, modern components
- ✅ Accessible
- ✅ Customizable
- ✅ Fast development

**State Management:** Zustand (lightweight)

### UI Layout

```
┌────────────────────────────────────────────────────────────┐
│  🐼 WWF Logo                                      [⚙️ 👤]  │
├─────────────┬──────────────────────────────────────────────┤
│             │                                              │
│ 📜 CHAT     │  💬 Main Chat Area                          │
│ HISTORY     │                                              │
│             │  ┌─────────────────────────────────────┐    │
│ + New Chat  │  │ User: What are the latest...        │    │
│             │  │ 🕐 20:00                            │    │
│ Session 1   │  └─────────────────────────────────────┘    │
│ 20:00 PM    │                                              │
│ 5 messages  │  ┌─────────────────────────────────────┐    │
│             │  │ 🤖 Assistant: Based on WWF...       │    │
│ Session 2   │  │ 📚 Sources: [1] [2]                │    │
│ 15:30 PM    │  │ 🕐 20:01                            │    │
│ 12 messages │  └─────────────────────────────────────┘    │
│             │                                              │
│             │  ┌─────────────────────────────────────┐    │
│             │  │ Type your message...          [📎] │    │
│             │  │ User: Can you export this as PDF?   │    │
│             │  └─────────────────────────────────────┘    │
│             │                                              │
│             │  ┌─────────────────────────────────────┐    │
│             │  │ 🤖 I've generated a PDF...          │    │
│             │  │ 📥 Download: chat_session.pdf       │    │
│             │  └─────────────────────────────────────┘    │
│             │                                              │
│             │  ┌─────────────────────────────────────┐    │
│             │  │ Type your message...                │    │
│             │  │                              [Send] │    │
│             │  └─────────────────────────────────────┘    │
└─────────────┴──────────────────────────────────────────────┘

Note: PDF export is conversational - triggered only when user asks

### Component Structure

```typescript
src/
├── app/
│   ├── chatbot/
│   │   ├── [sessionId]/
│   │   │   └── page.tsx           # Chat interface
│   │   ├── layout.tsx             # Chat layout wrapper
│   │   └── DownloadLink.tsx       # Show PDF download link (when generated)
│   └── api/
│       └── chatbot/               # API route proxies
├── components/
│   ├── chatbot/
│   │   ├── ChatInterface.tsx      # Main chat component
│   │   ├── MessageList.tsx        # Message display
│   │   ├── MessageInput.tsx       # Input component
│   │   ├── SessionList.tsx        # Left sidebar
│   │   ├── SourceCitation.tsx     # Show sources
│   │   └── PDFExport.tsx          # PDF export button
│   └── ui/                        # shadcn components
├── lib/
│   ├── api.ts                     # API client
│   ├── types.ts                   # TypeScript types
│   └── utils.ts                   # Utilities
└── stores/
    └── chatStore.ts               # Zustand store
```

### Key TypeScript Types

```typescript
// lib/types.ts
export interface UserContext {
  user_id: string;
  name: string;
  education: string;
  location: string;
}

export interface ChatMessage {
  message_id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  agent_used?: 'rag' | 'web_search' | 'hybrid';
  timestamp: string;
}

export interface Source {
  type: 'rag' | 'web_search';
  title: string;
  url?: string;
  excerpt: string;
}

export interface ChatSession {
  session_id: string;
  user_id: string;
  started_at: string;
  last_activity: string;
  message_count: number;
  preview?: string;
}

export interface SendMessageRequest {
  pdf_url?: string;  // Only present if user requested PDF export
  session_id: string;
  user_id: string;
  message: string;
}

export interface SendMessageResponse {
  message_id: string;
  response: string;
  sources: Source[];
  agent_used: string;
  timestamp: string;
}
```

---

## 📄 PDF Export Implementation
Conversational PDF Export

**Trigger:** User explicitly asks in chat (e.g., "Can you export this as PDF?", "Download this conversation")

**Flow:**
1. User sends message requesting PDF
2. Supervisor agent detects PDF export intent
3. Backend generates PDF from session history
4. Returns PDF download link in response
5. UI displays clickable download link in chat

**Library:**
**Library:** `pdfkit` (Node.js) or `reportlab` (Python backend)

**Recommendation:** Generate on backend (Python) for consistency

```python
# src/chatbot/pdf_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
from datetime import datetime

class ChatPDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.create_custom_styles()
    
    def create_custom_styles(self):
        # Custom styles for chat messages
        self.styles.add(ParagraphStyle(
            name='UserMessage',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor='#000000',
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='AssistantMessage',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor='#333333',
            leftIndent=20,
            spaceAfter=12
        ))
    
    def generate_pdf(
        self,
        session_id: str,
        user_context: dict,
        messages: list,
        output_path: str
    ):
        """Generate PDF from chat session"""
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        
        # Add WWF logo (if available)
        # logo = Image('path/to/wwf_logo.png', width=2*inch, height=1*inch)
        # story.append(logo)
        # story.append(Spacer(1, 0.5*inch))
        
        # Add title
        title = Paragraph(
            "<b>WWF Sustainability Chat Session</b>",
            self.styles['Title']
        )
        story.append(title)
        story.append(Spacer(1, 0.3*inch))
        
        # Add user info
        user_info = Paragraph(
            f"<b>User:</b> {user_context['name']}<br/>"
            f"<b>Location:</b> {user_context['location']}<br/>"
            f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}",
            self.styles['Normal']
        )
        story.append(user_info)
        story.append(Spacer(1, 0.5*inch))
        
        # Add messages
        for msg in messages:
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime('%I:%M %p')
            
            if msg['role'] == 'user':
                text = f"<b>You ({timestamp}):</b><br/>{msg['content']}"
                story.append(Paragraph(text, self.styles['UserMessage']))
            else:
                text = f"<b>WWF Assistant ({timestamp}):</b><br/>{msg['content']}"
                story.append(Paragraph(text, self.styles['AssistantMessage']))
                
                # Add sources if available
                if msg.get('sources'):
                    sources_text = "<b>Sources:</b><br/>"
                    for idx, source in enumerate(msg['sources'], 1):
                        sources_text += f"{idx}. {source['title']}<br/>"
                    story.append(Paragraph(sources_text, self.styles['Normal']))
            
            story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        return output_path
```

---

## 🔐 Security & Best Practices

### 1. Input Validation
```python
from pydantic import BaseModel, validator

class MessageRequest(BaseModel):
    session_id: str
    user_id: str
    message: str
    
    @validator('message')
    def validate_message(cls, v):
        if len(v) > 2000:
            raise ValueError('Message too long (max 2000 chars)')
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()
```

### 2. Rate Limiting
```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@router.post("/message", dependencies=[Depends(RateLimiter(times=20, seconds=60))])
async def send_message(...):
    # 20 messages per minute per user
    pass
```

### 3. Session Timeout
- Auto-expire sessions after 24 hours of inactivity
- Cleanup old sessions periodically

### 4. Prompt Injection Prevention
```python
def sanitize_user_input(message: str) -> str:
    """Prevent prompt injection attacks"""
    # Remove system instructions attempts
    forbidden_patterns = [
        "ignore previous instructions",
        "you are now",
        "system:",
        "assistant:",
    ]
    
    message_lower = message.lower()
    for pattern in forbidden_patterns:
        if pattern in message_lower:
            # Log attempt
            logger.warning(f"Prompt injection attempt detected: {message}")
            return "I'm here to answer sustainability questions."
    
    return message
```

---

## 📊 Monitoring & Analytics

### Track Metrics

```python
# Log every interaction
metrics = {
    "user_id": user_id,
    "session_id": session_id,
    "query_intent": intent,  # rag/web/hybrid
    "agent_used": agent_type,
    "response_time": elapsed_time,
    "user_location": location,
    "sources_count": len(sources),
    "timestamp": datetime.now()
}

# Log to analytics DB or service
analytics_logger.info(metrics)
```

### Dashboard Metrics
- Queries per day/hour
- Agent usage distribution (RAG vs Web vs Hybrid)
- Average response time
- Most common topics/queries
- User engagement (messages per session)
- Geographic distribution of users


---

## 🛠️ Technology Stack Summary

| Component | Technology | Reason |
|-----------|-----------|--------|
| Agent Framework | **LangGraph** | Best for complex routing workflows |
| Web Search | **TavilyAI** | Built for AI agents, clean results |
| Vector DB | ChromaDB | Already in use |
| Embeddings | OpenAI (text-embedding-3-small) | Existing choice |
| LLM | Groq (llama-3.3-70b-versatile) | Existing choice |
| Backend | FastAPI | Existing framework |
| Frontend | **Next.js 14 + TypeScript** | Production-ready, SEO, SSR |
| UI Library | **Tailwind + shadcn/ui** | Modern, accessible |
| Chat History | **SQLite** → PostgreSQL | Simple to start, scalable |
| PDF Generation | **reportlab** (Python) | Consistent backend generation |
| State Management | **Zustand** | Lightweight, TypeScript-friendly |

---

## 💡 Key Design Decisions

### 1. Why LangGraph?
- ✅ Perfect for stateful, multi-agent workflows
- ✅ Built-in routing and state management
- ✅ Easy to visualize agent flow
- ✅ Production-ready

### 2. Why TavilyAI over Google/Serper?
- ✅ Designed for LLM agents
- ✅ Returns summarized, relevant content
- ✅ Domain filtering support
- ✅ Lower cost for agent use cases

### 3. Why Next.js over React SPA?
- ✅ Better SEO (if needed)
- ✅ Server-side rendering for fast initial load
- ✅ Built-in API routes (optional BFF layer)
- ✅ Production optimizations out of the box

### 4. Why SQLite initially?
- ✅ No additional infrastructure
- ✅ File-based (easy backup)
- ✅ Fast for read-heavy workloads
- ✅ Easy migration path to PostgreSQL

---
