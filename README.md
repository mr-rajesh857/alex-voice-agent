# 💬 Alex — Chat-Driven AI Assistant Agent

A production-grade, chat-driven AI assistant powered by **LangGraph**, **LangChain**, **FastAPI**, **Next.js 15**, **FastMCP tool servers**, and **PostgreSQL (pgvector)**.

---

## 🏗️ Tech Stack & Architecture

- **Frontend**: Next.js 15 (App Router, TypeScript, Tailwind CSS, MediaRecorder VAD)
- **Backend API**: FastAPI, Uvicorn, Async SQLAlchemy 2.0, WebSockets
- **Agent Orchestrator**: LangGraph (Stateful graph branching, confirmation security gates, memory nodes)
- **LLM Engine**: Google Gemini API via `langchain-google-genai`
- **Tool Protocols**: FastMCP (Model Context Protocol) servers for Calendar, Contacts, Reminders, RAG Search, Email, and User Preferences
- **Database**: PostgreSQL 16 with `pgvector` extension for long-term semantic memory
- **Database GUI**: Adminer (web-based GUI for DB management at `http://localhost:8080`)
- **In-Memory Store**: Redis 7 (caching, session state & audio queue management)

---

## 📁 Repository Structure

```
alex-voice-agent/
├── backend/                        # FastAPI Gateway & LangGraph Orchestrator
│   ├── app/
│   │   ├── audio/                  # STT/TTS streaming & VAD processors
│   │   ├── core/                   # Security, JWT auth, config loader
│   │   ├── db/                     # Async SQLAlchemy models & session
│   │   ├── graph/                  # LangGraph nodes, state, edges, checkpointer
│   │   ├── llm/                    # Gemini client wrappers & prompts
│   │   ├── memory/                 # Vector memory retriever (pgvector)
│   │   ├── mcp_client/             # FastMCP tool callers
│   │   └── routers/                # REST & WebSocket endpoints
│   ├── requirements.txt
│   └── .env
│
├── frontend/                       # Next.js 14 Frontend App
│   ├── src/
│   │   ├── app/                    # App Router (/login, /register, dashboard /)
│   │   ├── components/             # Audio Waveform, Live Transcript, Chat UI
│   │   ├── context/                # AuthContext provider
│   │   └── lib/                    # API client with JWT bearer injection
│   └── package.json
│
├── mcp-servers/                    # FastMCP Tool Servers
│   ├── calendar-mcp/
│   ├── contacts-mcp/
│   ├── reminders-mcp/
│   ├── search-rag-mcp/
│   ├── email-messaging-mcp/
│   └── user-prefs-mcp/
│
├── infra/                          # PostgreSQL Init SQL & pgvector setup
│   └── postgres/init.sql
│
├── docker-compose.yml              # Docker Compose setup
├── .env.example                    # Environment template
└── voice-agent-project-plan.md     # Comprehensive Architectural Specification
```

---

## ⚡ Quick Start Guide (How to Run)

### Prerequisites
- [Docker](https://www.docker.com/) and Docker Compose installed
- Python 3.10+
- Node.js 18+ and npm

---

### Step 1: Environment Setup

Copy `.env.example` to `.env` in both the root directory and `backend/`:

```bash
# In Root directory
cp .env.example .env

# In Backend directory
cp backend/.env.example backend/.env
```

---

### Step 2: Start Infrastructure Services (PostgreSQL, Adminer, Redis via Docker)

In the root directory, start the database, Adminer GUI, and Redis containers:

```bash
docker compose up -d
```

- **PostgreSQL Database**: Port `5433` (`postgresql+asyncpg://alex_user:alex_password@localhost:5433/alex_db`)
- **Adminer DB GUI**: Open [http://localhost:8080](http://localhost:8080)
- **Redis Cache**: Port `6379` (`redis://localhost:6379/0`)

---

### Step 3: Start the Backend API (FastAPI)

In a new terminal window:

```bash
cd backend

# 1. Activate Python virtual environment
source ../.venv/bin/activate

# 2. Install backend dependencies (if not installed)
pip install -r requirements.txt

# 3. Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

- **Backend API**: `http://localhost:8000`
- **Swagger Documentation**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

---

### Step 4: Start the Frontend App (Next.js)

In another terminal window:

```bash
cd frontend

# 1. Install frontend dependencies (if not installed)
npm install

# 2. Start Next.js development server
npm run dev
```

- **Frontend Application**: Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🔑 Authentication Workflow

1. Open `http://localhost:3000` (Redirects to `/login`).
2. Click **"Create account"** to register a new user at `/register`.
3. Upon registration/login, a secure **JWT access token** is issued and stored in `localStorage`.
4. All frontend API calls automatically attach `Authorization: Bearer <token>`.

---

## 📜 Available NPM & Python Scripts

| Context | Command | Description |
| :--- | :--- | :--- |
| **Root** | `docker compose up -d postgres` | Starts PostgreSQL container with `pgvector` |
| **Backend** | `uvicorn app.main:app --reload --port 8000` | Starts FastAPI backend server |
| **Backend** | `pytest` | Runs backend test suite |
| **Frontend** | `npm run dev` | Runs Next.js frontend dev server |
| **Frontend** | `npm run build` | Builds frontend for production |

---

## 🔒 Security Configuration

- **`JWT_SECRET`**: Key used for signing/verifying JWT authentication tokens.
- **`ENCRYPTION_KEY`**: Key used for database-level encryption of third-party OAuth tokens.
