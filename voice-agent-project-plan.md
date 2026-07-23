# Project "Alex" — Voice-Driven AI Assistant Agent
### Full Production Project Plan & Architecture Specification

Stack: LangGraph + LangChain + Python + FastAPI + Next.js + PostgreSQL (pgvector) + FastMCP + Deepgram / ElevenLabs Audio + Gemini LLM

---

## 1. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   NEXT.JS FRONTEND                                     │
│  (MediaRecorder audio streaming, Web VAD, Live Transcript, Waveform, Confirmation UI)  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ WebSocket / Streamable HTTP
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FASTAPI GATEWAY                                     │
│     (JWT Auth, Audio Pipeline Gateway, STT/TTS Handlers, WebSocket Router, REST API)   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               LANGGRAPH AGENT BRAIN                                    │
│   (Stateful Graph: Memory Retrieval ➔ Intent Extraction ➔ Slot Check ➔ Confirmation Gate)│
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
2. `parse_intent` — Gemini extracts intent + entities (action, attendee, date, time, duration, query parameters).
3. `check_completeness` — Conditional edge:
   - If required slots missing ➔ go to `ask_clarification`.
   - If complete ➔ go to `resolve_entities`.
4. `ask_clarification` — Generates a targeted follow-up question ("Kis time pe meeting fix karni hai?"), returns audio/text to user, pauses graph.
5. `resolve_entities` — Calls `contacts-mcp` to resolve names, queries `calendar-mcp.find_free_slot` for vague time queries.
6. `confirm_action` — Hard security gate for create/update/delete side-effects. Generates spoken confirmation ("3 baje Alex ke saath meeting fix kar du?") and waits for user confirmation.
7. `execute_tool` — Dispatches call to the matching FastMCP server tool.
8. `store_memory` — Asynchronously extracts notable new user facts/preferences and writes to `pgvector`.
9. `handle_error` — Graceful fallback handler if tool or API fails.
10. `respond` — Prepares natural language response optimized for STT/TTS phrasing.

### Shared State Object Schema
```python
from typing import TypedDict, Any, List, Dict, Optional

class AgentState(TypedDict):
    session_id: str
    user_id: str
    conversation: List[Dict[str, str]]
    retrieved_memories: List[str]
    intent: Optional[str]
    entities: Dict[str, Any]
    missing_slots: List[str]
    pending_confirmation: bool
    confirmation_given: Optional[bool]
    tool_name: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]
    is_interrupted: bool
    error: Optional[str]
```

---

## 3. Audio & Voice Pipeline Specification

### Audio Stream & VAD Architecture
- **Client Capture**: WebRTC / `MediaRecorder` API streaming 16kHz PCM / Opus chunks over WebSocket.
- **Voice Activity Detection (VAD)**:
  - Client-side VAD (Web VAD / Silero WASM) for instant visual speech indicator.
  - Server-side VAD (Silero VAD) on audio stream to detect speech start/stop accurately.
- **STT (Speech-to-Text)**: Deepgram Nova-2 / Whisper Streaming WebSocket with word-level timestamps & language auto-detect.
- **TTS (Text-to-Speech)**: ElevenLabs WebSocket API / Deepgram Aura returning streamed audio chunks (MP3/Opus) directly to frontend player.

### Interruption (Barge-in) Control Flow
When the user speaks while the AI agent is outputting TTS audio:
1. Client VAD triggers speech start signal.
2. Client sends `{"type": "interrupt"}` message over WebSocket.
3. Backend immediately aborts active LLM generation stream and TTS synthesis task.
4. Backend clears audio queue and sets `is_interrupted = True` in `AgentState`.
5. Frontend clears current audio buffer playback instantly.

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
- `get_preferences()` — Fetches voice tone, TTS speed, timezone, language preferences.
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
    category VARCHAR(50), -- preference, relationship, fact
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sessions & Conversation Turns
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user, assistant, system
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

## 6. Multilingual & Hinglish Code-Switching Engine

- **STT Configuration**: Deepgram language set to `hi-Latn` / `multilingual` to support seamless Hindi + English switching.
- **LLM Prompting**: Prompts explicitly instruct Gemini to process Hinglish inputs (e.g. *"Kal subah 10 baje team sync fix kar do"*) and retain natural conversational Hinglish or clear English in response.
- **TTS Phrasing**: Output text is pre-processed for phonetic readability before being sent to TTS engines.

---

## 7. Repo & Folder Structure

```
alex-voice-agent/
├── backend/                        # FastAPI Backend & LangGraph Orchestrator
│   ├── app/
│   │   ├── audio/                  # STT streaming, TTS streaming, VAD processors
│   │   ├── core/                   # App config, security, JWT auth, logging
│   │   ├── db/                     # SQLAlchemy 2.0 async models, pgvector session, alembic migrations
│   │   ├── graph/                  # LangGraph nodes, state, edges, checkpointer
│   │   ├── llm/                    # Gemini client wrappers, prompt templates
│   │   ├── memory/                 # Vector memory indexing & retriever
│   │   ├── mcp_client/             # FastMCP Client bindings & tool callers
│   │   └── routers/                # WebSocket audio/chat endpoint, REST auth, history, settings
│   ├── tests/                      # Pytest unit & integration test suite
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                       # Next.js 14 Frontend App
│   ├── public/
│   ├── src/
│   │   ├── app/                    # App Router pages (dashboard, chat, history, settings)
│   │   ├── components/             # Audio Waveform, Live Transcript, Confirmation Modal, Chat UI
│   │   ├── hooks/                  # useAudioRecorder, useWebSocket, useVAD
│   │   ├── lib/                    # API client, audio utils
│   │   └── types/                  # TypeScript interfaces
│   ├── package.json
│   └── tailwind.config.js / globals.css
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
│   ├── docker-compose.yml          # Multi-container orchestration (Postgres, Backend, Frontend, MCP servers)
│   ├── postgres/                   # Init SQL scripts & pgvector setup
│   └── prometheus/                 # Monitoring metrics
│
├── docker-compose.yml              # Root Docker Compose for easy `docker compose up postgres`
└── voice-agent-project-plan.md     # Architectural Plan
```

---

## 8. Latency Budget & Observability

### Latency Budget Target (< 900ms Total Roundtrip)
- **STT Processing**: ~150-200ms
- **LangGraph Routing & Gemini TTFT**: ~300-400ms
- **TTS TTFB (Time to First Audio Byte)**: ~150-200ms
- **Total Latency**: ~650-800ms

### Observability & Evaluation Suite
- **LangSmith / OpenTelemetry**: Full trace from WebSocket ingress ➔ STT ➔ LangGraph Nodes ➔ FastMCP Tool Execution ➔ TTS streaming.
- **Latency Benchmarking**: Automated metrics logging for each stage of voice processing.
- **Eval Suite**: Continuous integration test harness simulating conversational turns to verify intent slot parsing and confirmation security gates.

---

## 9. Phased Implementation Roadmap

### Phase 1 — User Authentication & JWT Security (CURRENT FOCUS)
- User table schema with bcrypt password hashing.
- Backend FastAPI Auth REST APIs: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`.
- JWT Token generation & verification middleware (`get_current_user`).
- Next.js modern, responsive Auth Pages (`/login` & `/register`) with Tailwind CSS & persistent session token storage.

### Phase 2 — Core LangGraph Agent Engine (Text)
- Implement `AgentState` and LangGraph node structure.
- Integrate Gemini LLM wrapper and prompt templates.
- Implement clarification loop and strict confirmation gate.

### Phase 3 — FastMCP Tool Ecosystem Integration
- Build and containerize `calendar-mcp`, `contacts-mcp`, and `reminders-mcp`.
- Connect FastMCP client bindings to LangGraph `execute_tool` node.
- Implement `tool_call_audit` database logger.

### Phase 4 — Audio Pipeline & WebSockets
- Implement WebSocket audio streaming router in FastAPI with JWT connection upgrade auth.
- Integrate STT (Deepgram/Whisper) and TTS (ElevenLabs/Deepgram Aura) streaming.
- Add VAD and Barge-in interruption protocol.

### Phase 5 — Memory, Search & Extended MCPs
- Implement `user_memories` vector search with `pgvector`.
- Build `search-rag-mcp`, `email-messaging-mcp`, and `user-prefs-mcp`.
- Connect long-term memory retrieval node into LangGraph pre-execution state.

### Phase 6 — Frontend Voice Assistant Dashboard & Polish
- Build Next.js voice recording waveform component and live transcript stream.
- Build Confirmation Modal UI for side-effecting actions.
- Add session history view and settings dashboard.

