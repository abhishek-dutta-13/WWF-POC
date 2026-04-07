# 🌍 WWF Sustainability Assistant

An intelligent AI-powered chatbot and learning platform for WWF sustainability content, featuring RAG-based knowledge retrieval, real-time web search, and automated micro-learning generation.

**🚀 Live Demo**: [https://wwf-poc.onrender.com](https://wwf-poc.onrender.com)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The WWF Sustainability Assistant is a full-stack application that combines:

1. **AI Chatbot** - Conversational assistant with intelligent routing between knowledge base and web search
2. **Micro-Learning Generator** - RAG-powered educational content creation from WWF documents
3. **Session Management** - Persistent chat history stored in PostgreSQL
4. **Web UI** - React-based chat interface with session history sidebar

**Key Capabilities:**
- Answers sustainability questions using WWF knowledge base (circular economy, ESG, sustainable agriculture, palm oil)
- Falls back to web search for topics outside knowledge base or real-time information
- Generates comprehensive micro-learning modules from document corpus
- Exports conversations as PDF
- Integrates with Quickbase for educational content delivery

---

## ✨ Features

### 🤖 Chatbot Features

- **Intelligent Routing**: Supervisor agent routes queries to appropriate handler:
  - 📚 **RAG Agent**: Retrieves from WWF knowledge base (ChromaDB vector store)
  - 🌐 **Web Search Agent**: Searches web using Tavily/DuckDuckGo for current info
  - 🔀 **Hybrid Mode**: Combines both sources when needed
  
- **Smart Fallback**: Automatically switches to web search if RAG returns insufficient results

- **Session Management**:
  - Persistent chat history with PostgreSQL
  - Session history sidebar in UI
  - Resume previous conversations
  - Create new chat sessions

- **PDF Export**: Export conversations with metadata and sources

- **Multi-Model LLM Support**: 
  - Primary: Groq (Llama 4 Scout, Llama 3.3 70B, Llama Prompt Guard)
  - Fallback: OpenAI GPT-3.5 Turbo (lowest cost)

### 📚 Micro-Learning Features

- **RAG-Based Generation**: Creates structured educational modules from WWF documents
- **Category-Specific**: Filters content by category using metadata
- **Comprehensive Content**: 4-6 chapters per category, 250-400 words per micro-content
- **Quickbase Integration**: JSON output format for LMS integration
- **Multi-Model Fallback**: Groq → OpenAI for resilience

---

## 🏗 Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  React Chat UI (Tail wind CSS)                        │  │
│  │  - Chat interface with message history               │  │
│  │  - Session history sidebar                           │  │
│  │  - New chat / Close buttons                          │  │
│  └──────────────────┬───────────────────────────────────┘  │
└────────────────────┼──────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────┼──────────────────────────────────────┐
│                    ▼         Backend (FastAPI)            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Main API (main.py)                                  │ │
│  │  - Static file serving                               │ │
│  │  - CORS configuration                                │ │
│  │  - Router aggregation                                │ │
│  └─────┬────────────────────────┬───────────────────────┘ │
│        │                        │                          │
│   ┌────▼─────────┐         ┌────▼──────────────┐         │
│   │   Chatbot    │         │  Micro-Learning   │         │
│   │   Router     │         │     Router        │         │
│   └────┬─────────┘         └────┬──────────────┘         │
│        │                        │                          │
│  ┌─────▼───────────────────────▼──────────────────────┐  │
│  │         Agent Orchestration Layer                   │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  Supervisor Agent (Router)                    │  │  │
│  │  │  - Query analysis                             │  │  │
│  │  │  - Topic matching against KB scope            │  │  │
│  │  │  - Routes to: RAG / Web / Hybrid / PDF        │  │  │
│  │  └──────┬─────────────────┬─────────────────────┘  │  │
│  │         │                 │                         │  │
│  │    ┌────▼────┐       ┌────▼────┐      ┌──────────┐ │  │
│  │    │   RAG   │       │   Web   │      │ Response │ │  │
│  │    │  Agent  │       │  Search │      │  Agent   │ │  │
│  │    └────┬────┘       └────┬────┘      └──────────┘ │  │
│  │         │                 │                         │  │
│  └─────────┼─────────────────┼─────────────────────────┘  │
│            │                 │                            │
│     ┌──────▼────┐     ┌──────▼──────┐                    │
│     │ ChromaDB  │     │  Tavily/    │                    │
│     │  Vector   │     │ DuckDuckGo  │                    │
│     │  Store    │     │   Search    │                    │
│     └───────────┘     └─────────────┘                    │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Database Layer (PostgreSQL)                         │ │
│  │  - Users, ChatSessions, ChatMessages                 │ │
│  │  - SQLAlchemy ORM                                    │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Agent Workflow

```
User Query
    │
    ├──> Supervisor Agent (Routes based on query analysis)
    │     │
    │     ├──> RAG Agent (Knowledge Base Topics)
    │     │    - Circular economy, waste reduction
    │     │    - ESG factors, financial models
    │     │    - Sustainable agriculture, palm oil
    │     │    - Compliance, certifications
    │     │    │
    │     │    ├──> ChromaDB Query (top-10 chunks)
    │     │    ├──> Quality Check (<2 sources?)
    │     │    └──> [Fallback to Web Search if needed]
    │     │
    │     ├──> Web Search Agent (Current/Real-time Info)
    │     │    - Time-sensitive queries (latest, recent, 2026)
    │     │    - Location-specific questions
    │     │    - Topics outside KB scope
    │     │    │
    │     │    ├──> Tavily Search API (Primary)
    │     │    └──> DuckDuckGo (Fallback)
    │     │
    │     └──> PDF Export Agent
    │
    └──> Response Agent (Generates personalized response)
          - Combines RAG + Web context
          - User context (name, location, education)
          - Cites sources
```

---

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL (session & message storage)
- **ORM**: SQLAlchemy
- **Vector Store**: ChromaDB (persistent local storage)
- **Embeddings**: OpenAI `text-embedding-3-small`

### AI & LLM
- **Primary LLM**: Groq
  - `meta-llama/llama-4-scout-17b-16e-instruct`
  - `meta-llama/llama-prompt-guard-2-22m`
  - `llama-3.3-70b-versatile`
- **Fallback LLM**: OpenAI GPT-3.5 Turbo
- **Search**: Tavily API (primary), DuckDuckGo (fallback)

### Frontend
- **UI Library**: React 18 (via CDN)
- **Styling**: Tailwind CSS
- **Build**: Babel (JSX transpilation in-browser)

### DevOps
- **Hosting**: Render.com (free tier)
- **CI/CD**: GitHub → Render auto-deploy
- **Environment**: `.env` for secrets

---

## 📁 Project Structure

```
WWF/
├── README.md                           # This file
├── render.yaml                         # Render deployment configuration
├── requirements.txt                    # Python dependencies
├── .gitignore                          # Git exclusions
├── .env.example                        # Environment variable template
│
├── src/
│   ├── main.py                         # FastAPI application entry point
│   │
│   ├── routers/
│   │   ├── chatbot_router.py          # Chatbot API endpoints
│   │   └── microlearning_router.py    # Micro-learning endpoints
│   │
│   ├── chatbot/
│   │   ├── database.py                 # PostgreSQL models & session
│   │   ├── models.py                   # Pydantic schemas
│   │   ├── pdf_generator.py           # PDF export functionality
│   │   │
│   │   └── agents/
│   │       ├── graph.py                # Workflow orchestrator
│   │       ├── supervisor.py           # Query router
│   │       ├── rag_agent.py            # ChromaDB retrieval
│   │       ├── web_search_agent.py     # Web search
│   │       └── response_agent.py       # Response generation
│   │
│   └── services/
│       └── microlearning_generator.py  # RAG-based module generator
│
├── chatbot-ui/
│   ├── launcher.html                   # Chat launcher page
│   ├── index.html                      # Main chat interface
│   └── wwf-logo-new.jpg               # WWF branding
│
├── vector_store/                       # ChromaDB storage (committed to repo)
│   └── chroma.sqlite3                  # Vector database
│
├── data/                               # Source documents (by category)
│   ├── category_file/
│   │   └── categories.csv             # Category→CourseID mapping
│   ├── circular_economy_and_waste_reduction/
│   ├── sustainability_strategy_and_compliance/
│   └── sustainable_agriculture_and_natural_resources/
│
└── Notebook/                           # Jupyter setup & testing
    ├── 01_data_ingestion_vector_store.ipynb
    └── 02_test_microlearning_generation.ipynb
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database (local or cloud)
- API Keys:
  - Groq API key (free at [console.groq.com](https://console.groq.com))
  - OpenAI API key (for embeddings & fallback)
  - Tavily API key (optional, for web search)

### Local Development

1. **Clone Repository**
   ```bash
   git clone https://github.com/abhishek-dutta-13/WWF-POC.git
   cd WWF
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv rag
   .\rag\Scripts\activate  # Windows
   # source rag/bin/activate  # Linux/Mac
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database URL
   ```

5. **Initialize Database**
   ```bash
   # Database tables are auto-created on first run
   python -c "from src.chatbot.database import Base, engine; Base.metadata.create_all(engine)"
   ```

6. **Run Development Server**
   ```bash
   cd src
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access Application**
   - Chatbot Launcher: http://localhost:8000/
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

---

## 📡 API Endpoints

### Health & Status

- `GET /health` - Health check with component status

### Chatbot Endpoints

- `POST /chatbot/session/init` - Initialize new chat session
- `POST /chatbot/message` - Send message and get AI response
- `GET /chatbot/session/{session_id}/history` - Get chat history
- `GET /chatbot/sessions/{user_id}` - Get user's chat sessions
- `GET /chatbot/download/{filename}` - Download exported PDF

### Micro-Learning Endpoints

- `POST /microlearning/generate` - Generate micro-learning module
- `POST /microlearning-quickbase` - Generate for Quickbase integration

### Example: Send Chat Message

```bash
curl -X POST "https://wwf-poc.onrender.com/chatbot/message" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-123",
    "user_id": "user-001",
    "message": "What are circular economy principles?"
  }'
```

**Response:**
```json
{
  "message_id": "msg-abc",
  "response": "According to WWF documents, circular economy principles...",
  "sources": [
    {
      "type": "rag",
      "title": "WWF Document",
      "excerpt": "The circular economy is a systemic approach..."
    }
  ],
  "agent_used": "rag",
  "timestamp": "2026-04-08T10:30:00Z"
}
```

---

## 🌐 Deployment

### Deploy to Render

1. **Fork/Push to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/wwf-poc.git
   git push -u origin main
   ```

2. **Create Render Web Service**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Render auto-detects `render.yaml` configuration

3. **Configure Environment Variables** (in Render dashboard)
   - See [Environment Variables](#environment-variables) section below

4. **Deploy**
   - Click "Create Web Service"
   - Render builds and deploys automatically
   - Auto-deploys on every GitHub push

### Render Configuration (`render.yaml`)

```yaml
services:
  - type: web
    name: wwf-poc
    runtime: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "cd src && uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

---

## 🔐 Environment Variables

Create a `.env` file (local) or add to Render dashboard (production):

```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# OpenAI (embeddings & fallback LLM)
OPENAI_API_KEY=sk-...

# Groq (primary LLM)
GROQ_API_KEY=gsk_...

# Tavily (web search)
TAVILY_API_KEY=tvly-...

# Application (optional)
COLLECTION_NAME=wwf_knowledge_base
LOG_LEVEL=INFO
```

### Getting API Keys

- **Groq**: [console.groq.com](https://console.groq.com) (free tier available)
- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Tavily**: [tavily.com](https://tavily.com) (optional, has free tier)
- **PostgreSQL**: Render provides free PostgreSQL database

---

## 🔗 Quickbase Integration

### Chatbot Integration Flow

**Step 1: Quickbase Form Captures User Data**
- User ID
- Name  
- Education/Background
- Location

**Step 2: Quickbase Pipeline POSTs to API**
```javascript
// Quickbase Pipeline Action: HTTP POST
URL: https://wwf-poc.onrender.com/chatbot/session/init
Method: POST
Headers:
  Content-Type: application/json
Body:
{
  "user_id": "{{user_id}}",
  "name": "{{name}}",
  "education": "{{education}}",
  "location": "{{location}}"
}
```

**Step 3: Get Session ID from Response**
```json
{
  "session_id": "abc-123-def-456",
  "user_id": "user_001",
  "message": "Chat session initialized successfully",
  "welcome_message": "Hello! I'm here to help..."
}
```

**Step 4: Open Chat Window**
```javascript
// Quickbase Pipeline Action: Open URL
URL: https://wwf-poc.onrender.com/chat?session_id={{response.session_id}}&user_id={{user_id}}
Target: New Window
```

**Result**: Chat window opens automatically with user's session initialized!

### Example Quickbase Pipeline

```yaml
Trigger: Record Created/Updated
Actions:
  1. HTTP POST Request
     - URL: https://wwf-poc.onrender.com/chatbot/session/init
     - Body: User details JSON
     - Save response to variable: init_response
  
  2. Open URL
     - URL: https://wwf-poc.onrender.com/chat?session_id={{init_response.session_id}}&user_id={{user_id}}
     - Target: New browser window
```

---

## 🧪 Testing

### Test Chatbot Locally

```bash
# Test RAG query
curl -X POST "http://localhost:8000/chatbot/message" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "user_id": "test-user",
    "message": "What is circular economy?"
  }'

# Test web search query
curl -X POST "http://localhost:8000/chatbot/message" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "user_id": "test-user",
    "message": "Latest WWF initiatives in 2026"
  }'
```

### Test Micro-Learning

```bash
curl -X POST "http://localhost:8000/microlearning-quickbase" \
  -H "Content-Type: application/json" \
  -d '{"category": "circular_economy_and_waste_reduction"}'
```

---

## 🐛 Troubleshooting

### Vector Store Issues
- **Error**: "Collection not found"
  - **Fix**: Run `Notebook/01_data_ingestion_vector_store.ipynb` to create vector store
  - **Fix**: Ensure `vector_store/` directory exists in repository

### Database Connection
- **Error**: "Could not connect to PostgreSQL"
  - **Fix**: Check `DATABASE_URL` in environment variables
  - **Fix**: Ensure PostgreSQL service is running

### API Rate Limits
- **Groq**: Free tier has rate limits
  - **Fix**: System automatically falls back to next model (llama-prompt-guard → llama-3.3-70b → gpt-3.5-turbo)
  - Check logs for model usage: `🚀 Attempt X/4: Using Groq model '...'`

### Session History Not Loading
- **Error**: Sessions not appearing in sidebar
  - **Fix**: Check PostgreSQL connection
  - **Fix**: Verify `/chatbot/sessions/{user_id}` endpoint returns data
  - **Fix**: Clear browser cache and reload

### Deployment Fails
- **Error**: Build fails on Render
  - **Fix**: Verify `requirements.txt` is present
  - **Fix**: Check Render build logs for specific errors
  - **Fix**: Ensure `src/main.py` exists and is correct

---

## 📚 Additional Documentation

- **[QUICKBASE.md](QUICKBASE.md)** - Quickbase integration guide
- **[MICROLEARNING_README.md](MICROLEARNING_README.md)** - Detailed micro-learning docs
- **API Documentation**: Visit `/docs` on your deployed instance

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is proprietary to WWF and Accenture.

---

## 👥 Authors

- **Abhishek Dutta** - Development - [abhishek.j.dutta@accenture.com](mailto:abhishek.j.dutta@accenture.com)

---

## 🙏 Acknowledgments

- WWF for sustainability content and guidelines
- Groq for free LLM API access
- Render for free hosting tier
- OpenAI for embeddings and fallback LLM
