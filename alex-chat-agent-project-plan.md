# Project "Alex" — Chat-Driven AI Assistant Agent
### Full Production Project Plan & Architecture Specification

Stack: LangGraph + LangChain + Python + FastAPI + Next.js + PostgreSQL (pgvector) + FastMCP + Gemini LLM + WebSockets

---

## 1. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   NEXT.JS CHAT FRONTEND                                │
│   (Streaming Chat UI, Markdown Renderer, Confirmation Buttons, Typing Indicator)       │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ WebSocket / HTTP Stream
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FASTAPI GATEWAY                                     │
│     (JWT Auth, Chat Stream Handlers, WebSocket Router, History REST APIs)              │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               LANGGRAPH AGENT BRAIN                                    │
│  (Stateful Graph: Memory Retrieval ➔ Intent Extraction ➔ Slot Check ➔ Confirmation Gate)│
└───────────┬───────────────────────────────┬────────────────────────────┬───────────────┘
            │                               │                            │
            ▼                               ▼                            ▼
┌──────────────────────┐        ┌──────────────────────┐      ┌──────────────────────┐
│     calendar-mcp     │        │     contacts-mcp     │      │    reminders-mcp     │
│  (FastMCP Server)    │        │  (FastMCP Server)    │      │  (FastMCP Server)    │
└───────────┬──────────┘        └───────────┬──────────┘      └───────────┬──────────┘
            │                               │                            │
            ├───────────────────────────────┼────────────────────────────┤
            │                               │                            │
            ▼                               ▼                            ▼
┌──────────────────────┐        ┌──────────────────────┐      ┌──────────────────────┐
│    search-rag-mcp    │        │ email-messaging-mcp  │      │   user-prefs-mcp     │
│  (FastMCP Server)    │        │  (FastMCP Server)    │      │  (FastMCP Server)    │
└───────────┬──────────┘        └───────────┬──────────┘      └───────────┬──────────┘
            │                               │                            │
            └───────────────────────────────┴────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              POSTGRESQL + PGVECTOR                                     │
│    (Users, OAuth Tokens, LangGraph Checkpoints, Tool Audit Logs, Vector Memories)       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. LangGraph Orchestration Design

The core brain is modeled as a stateful graph (not a linear chain).

### Graph Nodes & Workflow
1. `retrieve_memories` — Queries `pgvector` for user preferences, facts, and relevant context based on current query.
2. `parse_intent` — Gemini extracts intent + entities (action, attendee, date, time, duration, query parameters) from current turn + conversation context.
3. `check_completeness` — Conditional edge:
   - If required slots missing ➔ go to `ask_clarification`.
   - If complete ➔ go to `resolve_entities`.
4. `ask_clarification` — Generates a targeted follow-up question ("Kis time pe meeting schedule karni hai?"), returns message to chat stream, pauses graph state.
5. `resolve_entities` — Calls `contacts-mcp` to resolve contact names, queries `calendar-mcp.find_free_slot` for vague time queries.
6. `confirm_action` — Hard security gate for create/update/delete side-effects. Emits an interactive confirmation payload to the frontend ("3 baje Alex ke saath meeting schedule kar du? [Confirm] [Cancel]") and waits for user response.
7. `execute_tool` — Dispatches call to the matching FastMCP server tool.
8. `store_memory` — Asynchronously extracts notable new user facts/preferences and writes to `pgvector`.
9. `handle_error` — Graceful fallback handler if tool or API fails.
10. `respond` — Prepares natural, well-formatted Markdown response for the Chat UI.

### Shared State Object Schema
```python
from typing import TypedDict, Any, List, Dict, Optional

class Message(TypedDict):
    role: str       # "user", "assistant", "system", "tool"
    content: str
    timestamp: Optional[str]

class AgentState(TypedDict):
    session_id: str
    user_id: str
    user_name: Optional[str]
    input_text: str
    conversation: List[Message]
    retrieved_memories: List[str]
    intent: Optional[str]
    entities: Dict[str, Any]
    missing_slots: List[str]
    requires_confirmation: bool
    pending_confirmation: bool
    confirmation_given: Optional[bool]
    tool_name: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]
    final_response: Optional[str]
    error: Optional[str]
```

---

## 3. Real-Time Chat Protocol & Streaming Architecture

### Message Payload Types over WebSocket (`/ws/chat`):
1. **User Text Message**:
   ```json
   { "type": "text", "content": "Book a meeting with Rahul tomorrow at 3 PM" }
   ```
2. **Server Token Stream** (Real-time LLM streaming):
   ```json
   { "type": "stream_delta", "delta": "I am checking " }
   ```
3. **Interactive Confirmation Request**:
   ```json
   {
     "type": "confirmation_request",
     "action": "create_calendar_event",
     "summary": "Schedule meeting with Rahul tomorrow at 3:00 PM",
     "payload": { "title": "Meeting with Rahul", "start": "2026-07-24T15:00:00" }
   }
   ```
4. **User Confirmation Reply**:
   ```json
   { "type": "confirmation_response", "approved": true }
   ```

---

## 4. MCP Tool Servers Ecosystem (FastMCP)

Each tool server is built using FastMCP and containerized independently.

### 1. `calendar-mcp`
- `create_event(title, start, end, attendees)`
- `find_free_slot(date, duration, preferred_time=None)`
- `list_events(date_range)`
- `reschedule_event(event_id, new_start)`
- `cancel_event(event_id)` *(Requires confirmation flag)*

### 2. `contacts-mcp`
- `resolve_person(name)` — Fuzzy search against user contacts, returning ranked candidate list.
- `add_contact(name, email, phone)`
- `get_contact_details(contact_id)`

### 3. `reminders-mcp`
- `set_reminder(text, time)`
- `list_reminders(status='pending')`
- `complete_reminder(reminder_id)`

### 4. `search-rag-mcp`
- `web_search(query)` — Tavily / Serper API integration for real-time web search.
- `search_documents(query)` — Semantic search over user uploaded documents / notes.

### 5. `email-messaging-mcp`
- `draft_email(to, subject, body)`
- `send_email(draft_id)` *(Requires confirmation gate)*
- `send_slack_message(channel, message)` *(Requires confirmation gate)*

### 6. `user-prefs-mcp`
- `get_preferences()` — Fetches theme, persona tone, timezone, language preferences.
- `update_preference(key, value)`

---

## 5. Database Schema (PostgreSQL + pgvector)

```sql
-- Enable vector extension for memory
CREATE EXTENSION IF NOT EXISTS vector;

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OAuth Tokens (encrypted)
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    access_token_enc TEXT NOT NULL,
    refresh_token_enc TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Long-Term User Memories (Vector Search)
CREATE TABLE user_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    memory_text TEXT NOT NULL,
    category VARCHAR(50),
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sessions & Conversation Turns
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'New Chat',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user, assistant, system, tool
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- LangGraph State Checkpoint Table
CREATE TABLE agent_state_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    state_json JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tool Execution Audit Log
CREATE TABLE tool_call_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    input_json JSONB NOT NULL,
    output_json JSONB,
    status VARCHAR(20) NOT NULL, -- success, failure, denied
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. Repo & Folder Structure

```
alex-voice-agent/
├── backend/                        # FastAPI Backend & LangGraph Orchestrator
│   ├── app/
│   │   ├── core/                   # App config (os.getenv), security, JWT auth
│   │   ├── db/                     # SQLAlchemy 2.0 async models, pgvector session
│   │   ├── graph/                  # LangGraph nodes, state, edges, checkpointer
│   │   ├── llm/                    # Gemini client wrappers, prompt templates
│   │   ├── memory/                 # Vector memory indexing & retriever
│   │   ├── mcp_client/             # FastMCP Client bindings & tool callers
│   │   └── routers/                # WebSocket chat endpoint, REST auth, history
│   ├── tests/                      # Pytest unit & integration test suite
│   ├── requirements.txt
│   └── .env
│
├── frontend/                       # Next.js 15 Frontend App
│   ├── src/
│   │   ├── app/                    # App Router (/login, /register, chat dashboard /)
│   │   ├── components/             # Chat UI, Message Bubbles, Interactive Confirmation Card
│   │   ├── context/                # AuthContext provider
│   │   ├── hooks/                  # useWebSocketChat
│   │   ├── lib/                    # API client with JWT bearer injection
│   │   └── types/                  # TypeScript interfaces
│   ├── package.json
│   └── .env.local
│
├── mcp-servers/                    # Standalone FastMCP Tool Servers
│   ├── calendar-mcp/
│   ├── contacts-mcp/
│   ├── reminders-mcp/
│   ├── search-rag-mcp/
│   ├── email-messaging-mcp/
│   └── user-prefs-mcp/
│
├── infra/                          # Infrastructure & Deployment
│   └── postgres/                   # Init SQL scripts & pgvector setup
│
├── docker-compose.yml              # Local Docker infrastructure (postgres, adminer, redis)
└── voice-agent-project-plan.md     # Architectural Plan
```

---

## 7. Phased Implementation Roadmap

### Phase 1 — User Authentication & JWT Security (COMPLETED)
- User table schema with bcrypt password hashing.
- Backend FastAPI Auth REST APIs: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`.
- JWT Token generation & verification middleware (`get_current_user`).
- Next.js modern, responsive Auth Pages (`/login` & `/register`) with persistent session token storage.

### Phase 2 — Core LangGraph Chat Agent Engine (CURRENT FOCUS)
- Implement `AgentState` and LangGraph node structure for text chat.
- Integrate Gemini LLM wrapper, streaming token generation, and prompt templates.
- Implement clarification loop and interactive confirmation gate.

### Phase 3 — FastMCP Tool Ecosystem Integration
- Build and containerize `calendar-mcp`, `contacts-mcp`, and `reminders-mcp`.
- Connect FastMCP client bindings to LangGraph `execute_tool` node.
- Implement `tool_call_audit` database logger.

### Phase 4 — Real-time Chat UI & WebSocket Streaming
- Implement WebSocket chat endpoint (`/ws/chat`) in FastAPI with JWT token upgrade auth.
- Build Next.js Chat interface with streaming markdown response, typing indicator, and session history sidebar.
- Build interactive Confirmation Modal / Card UI for side-effecting actions.

### Phase 5 — Memory, RAG Search & Extended MCPs
- Implement `user_memories` vector search with `pgvector`.
- Build `search-rag-mcp`, `email-messaging-mcp`, and `user-prefs-mcp`.
- Connect long-term memory retrieval node into LangGraph pre-execution state.
