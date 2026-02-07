# SupportMind AI — Implementation Plan

**Date**: 2026-02-07
**Challenge**: RealPage SupportMind AI (Hack-Nation 4th Global AI Hackathon)
**Repo**: alpine-vector-minds

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Team Structure & Responsibilities](#2-team-structure--responsibilities)
3. [Database Team](#3-database-team)
4. [Backend API Team](#4-backend-api-team)
5. [AI Agents Team](#5-ai-agents-team)
6. [Frontend Team](#6-frontend-team)
7. [Data Import Pipeline](#7-data-import-pipeline)
8. [Integration Points & Contracts](#8-integration-points--contracts)
9. [Development Order & Dependencies](#9-development-order--dependencies)
10. [Environment & Configuration](#10-environment--configuration)
11. [Demo Script](#11-demo-script)

---

## 1. Architecture Overview

### What We're Building

A **self-learning support intelligence layer** with two hero features:

1. **Intelligent Triage Copilot** — Support agent asks a question, system classifies it (SCRIPT / KB / TICKET), retrieves the best match via vector search, and shows the answer with full provenance.
2. **Self-Learning Knowledge Loop** — When a resolved ticket has no matching KB article, the system detects the gap, auto-generates a draft KB article from the ticket + conversation + script, and puts it through a human review workflow.

### System Flow

```
                                    ┌─────────────────────────────┐
                                    │       FRONTEND (Next.js)    │
                                    │                             │
                                    │  ┌─────────┐ ┌───────────┐ │
                                    │  │ Copilot  │ │ Knowledge │ │
                                    │  │  Page    │ │ Base Page │ │
                                    │  └────┬─────┘ └─────┬─────┘ │
                                    │  ┌────┴─────┐ ┌─────┴─────┐ │
                                    │  │ Learning │ │ Dashboard │ │
                                    │  │ Feed Page│ │   Page    │ │
                                    │  └────┬─────┘ └─────┬─────┘ │
                                    └───────┼─────────────┼───────┘
                                            │  REST API   │
                                    ┌───────┼─────────────┼───────┐
                                    │       ▼   BACKEND   ▼       │
                                    │                             │
                                    │  ┌──────────────────────┐   │
                                    │  │   API Routes (v1)    │   │
                                    │  │  /copilot  /knowledge│   │
                                    │  │  /learning /dashboard│   │
                                    │  └──────────┬───────────┘   │
                                    │             │               │
                                    │  ┌──────────▼───────────┐   │
                                    │  │     AI Agents        │   │
                                    │  │  Triage  │ GapDetect │   │
                                    │  │  KBGen   │ QAScore   │   │
                                    │  └──────────┬───────────┘   │
                                    │             │               │
                                    │  ┌──────────▼───────────┐   │
                                    │  │  Embedding Service   │   │
                                    │  │  + Vector Search     │   │
                                    │  └──────────┬───────────┘   │
                                    │             │               │
                                    └─────────────┼───────────────┘
                                                  │
                                    ┌─────────────▼───────────────┐
                                    │   PostgreSQL + pgvector     │
                                    │                             │
                                    │  knowledge_articles (+ vec) │
                                    │  scripts (+ vec)            │
                                    │  tickets, conversations     │
                                    │  questions (ground truth)   │
                                    │  kb_lineage, learning_events│
                                    └─────────────────────────────┘
```

### Key Design Decisions

- **Classification before retrieval**: The 1,000 ground-truth questions show 70% need scripts, 21% need KB, 9% need ticket resolutions. We classify first, then search the correct pool — this outperforms naive "search everything."
- **pgvector for all vector search**: No external vector DB needed. We already have PostgreSQL + pgvector in Docker.
- **OpenAI `text-embedding-3-small`** (1536 dims): Already configured in our embedding service.
- **GPT-5** for LLM tasks (classification, KB generation, QA scoring): Via existing OpenAI integration.
- **Human-in-the-loop**: Learning events require explicit approval before KB articles become searchable.

---

## 2. Team Structure & Responsibilities

| Team | Scope | Key Files |
|------|-------|-----------|
| **Database** | Schema, models, migrations, data import script | `backend/vector_db/models/`, `backend/scripts/` |
| **Backend API** | FastAPI routes, Pydantic schemas, endpoint logic | `backend/api/v1/` |
| **AI Agents** | LLM agents, RAG pipeline, vector search functions | `backend/agents/`, `backend/vector_db/` |
| **Frontend** | Next.js pages, components, API client extensions | `frontend/web/src/` |

### Cross-Team Dependencies

```
Database ──────► Backend API ──────► Frontend
    │                 │
    └──► AI Agents ───┘
```

- **Database** is the foundation — everyone depends on the models being defined first.
- **AI Agents** and **Backend API** can work in parallel once models exist. The API team can stub agent calls.
- **Frontend** can start immediately using the API contracts defined below. Mock the endpoints locally if needed.

---

## 3. Database Team

### 3.1 New SQLAlchemy Models

All models go in `backend/vector_db/models/`. Follow the existing `user.py` pattern: SQLAlchemy 2.0 Mapped types, UUID primary keys, timezone-aware timestamps.

**Important**: After creating each model file, import it in `backend/vector_db/models/__init__.py` so `Base.metadata.create_all()` picks it up.

#### `backend/vector_db/models/knowledge_article.py`

```python
class SourceType(StrEnum):
    SEED_KB = "SEED_KB"
    SYNTH_FROM_TICKET = "SYNTH_FROM_TICKET"

class ArticleStatus(StrEnum):
    ACTIVE = "Active"
    DRAFT = "Draft"
    ARCHIVED = "Archived"

class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[str]              # PK, e.g. "KB-3FFBFE3C70" or "KB-SYN-0001"
    title: Mapped[str]           # Article title
    body: Mapped[str]            # Full article text (Text column)
    source_type: Mapped[str]     # SEED_KB | SYNTH_FROM_TICKET
    status: Mapped[str]          # Active | Draft | Archived
    category: Mapped[str | None] # e.g. "Advance Property Date"
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    version: Mapped[int]         # default=1, increment on update
    embedding: Mapped[...]       # pgvector Vector(1536), nullable
```

**Column details from dataset**:
- `id`: String, format `KB-{hex10}` for seed, `KB-SYN-{0001}` for synthetic. Max length 20.
- `title`: String(500). Avg ~80 chars, max ~180 chars.
- `body`: Text. Avg ~800 chars for seed KB, up to ~2000 chars.
- `source_type`: String(30). Two values: `SEED_KB` (3,046 rows), `SYNTH_FROM_TICKET` (161 rows).
- `status`: String(20). All are `Active` in dataset.
- `category`: String(100). Nullable. Present on synthetic articles.
- `version`: Integer, default 1.
- `embedding`: pgvector `Vector(1536)`. Nullable (populated by embedding pipeline).

**Indexes**:
- Primary key on `id`
- Index on `source_type` (filter queries)
- Index on `status` (filter active articles)
- Index on `category` (filter by category)
- IVFFlat index on `embedding` using cosine distance (after data import, with `lists=80`)

#### `backend/vector_db/models/script.py`

```python
class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[str]              # PK, e.g. "SCRIPT-0001"
    title: Mapped[str]           # Script title / description
    category: Mapped[str]        # e.g. "Certifications", "Advance Property Date"
    module: Mapped[str | None]   # e.g. "Compliance / Certifications"
    script_text: Mapped[str]     # Full script with placeholders (Text column)
    placeholders: Mapped[str | None]  # JSON array of placeholder names used
    created_at: Mapped[datetime]
    embedding: Mapped[...]       # pgvector Vector(1536), nullable
```

**Column details from dataset**:
- `id`: String(20). Format `SCRIPT-{0001-0714}`.
- `title`: String(200). Often same as category path, e.g. "Compliance / Certifications".
- `category`: String(100). 7 unique values: Certifications, Advance Property Date, General, HAP/Voucher Processing, etc.
- `module`: String(100). Nullable. More granular than category.
- `script_text`: Text. SQL scripts with `<PLACEHOLDER>` tokens. Avg 798 chars, max ~2000.
- `placeholders`: Text/JSON. Extracted list of placeholders found in script_text (computed on import).

**Indexes**:
- Primary key on `id`
- Index on `category`
- IVFFlat index on `embedding` with `lists=27`

#### `backend/vector_db/models/ticket.py`

```python
class TicketPriority(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class CaseType(StrEnum):
    INCIDENT = "Incident"
    HOW_TO = "How-To"
    TRAINING = "Training"

class RootCause(StrEnum):
    DATA_INCONSISTENCY = "Data inconsistency requiring backend fix"
    KNOWLEDGE_GAP = "Knowledge gap / workflow guidance"
    CONFIGURATION = "Configuration / setup"

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str]                     # PK = Ticket_Number, e.g. "CS-38908386"
    conversation_id: Mapped[str]        # FK to conversations, unique
    priority: Mapped[str]               # Low | Medium | High | Critical
    tier: Mapped[int]                   # 1, 2, or 3
    module: Mapped[str]                 # e.g. "Accounting / Date Advance"
    category: Mapped[str]               # e.g. "Advance Property Date"
    case_type: Mapped[str]              # Incident | How-To | Training
    account_name: Mapped[str]           # e.g. "Oak & Ivy Management"
    property_name: Mapped[str]          # e.g. "Heritage Point"
    property_city: Mapped[str]
    property_state: Mapped[str]         # 2-letter state code
    contact_name: Mapped[str]
    contact_role: Mapped[str]           # e.g. "Accounting Clerk"
    subject: Mapped[str]                # Ticket subject line
    description: Mapped[str]            # Issue description (Text)
    resolution: Mapped[str]             # Resolution text (Text)
    root_cause: Mapped[str]             # One of 3 root cause values
    tags: Mapped[str]                   # Comma-separated tag string
    kb_article_id: Mapped[str | None]   # FK to knowledge_articles (nullable)
    script_id: Mapped[str | None]       # FK to scripts (nullable)
    generated_kb_article_id: Mapped[str | None]  # FK to knowledge_articles (the synth article)
    created_at: Mapped[datetime]
    closed_at: Mapped[datetime]
```

**Column details from dataset**:
- `id`: String(20). Format `CS-{8digits}`. 400 rows.
- `conversation_id`: String(20). Format `CONV-{10chars}`. 1:1 with tickets.
- `priority`: String(10). 4 values: Medium (37%), High (34%), Low (17%), Critical (13%).
- `tier`: Integer. Range 1-3, mean 2.1.
- `module`: String(50). 17 unique values.
- `category`: String(50). 14 unique values.
- `case_type`: String(20). 3 values: Incident (62%), How-To (21%), Training (17%).
- `resolution`: Text. 18 unique template-based resolutions. Avg 418 chars.
- `root_cause`: String(50). 3 values: backend fix (40%), knowledge gap (30%), config (30%).
- `kb_article_id`: String(20). Nullable (87 nulls / 313 populated). Points to existing KB article used.
- `script_id`: String(20). Nullable (239 nulls / 161 populated). Points to Tier 3 script used.
- `generated_kb_article_id`: String(20). Nullable (239 nulls / 161 populated). Points to synthetic KB generated from this ticket.

**Indexes**:
- Primary key on `id`
- Unique index on `conversation_id`
- Index on `category`
- Index on `tier`
- Index on `priority`
- FK index on `kb_article_id`
- FK index on `script_id`

#### `backend/vector_db/models/conversation.py`

```python
class Channel(StrEnum):
    CHAT = "Chat"
    PHONE = "Phone"

class Sentiment(StrEnum):
    NEUTRAL = "Neutral"
    RELIEVED = "Relieved"
    CURIOUS = "Curious"
    FRUSTRATED = "Frustrated"

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str]              # PK = Conversation_ID, e.g. "CONV-O2RAK1VRJN"
    ticket_id: Mapped[str]       # FK to tickets.id (Ticket_Number)
    channel: Mapped[str]         # Chat | Phone
    customer_role: Mapped[str]   # e.g. "Accounting Clerk"
    agent_name: Mapped[str]      # e.g. "Alex"
    category: Mapped[str]        # e.g. "Advance Property Date"
    issue_summary: Mapped[str]   # Short issue description
    transcript: Mapped[str]      # Full conversation text (Text column)
    sentiment: Mapped[str]       # Neutral | Relieved | Curious | Frustrated
    started_at: Mapped[datetime]
    ended_at: Mapped[datetime]
```

**Column details from dataset**:
- `id`: String(20). Format `CONV-{10chars}`. 400 rows, all unique.
- `ticket_id`: String(20). 1:1 with tickets.
- `channel`: String(10). Chat (56%), Phone (44%).
- `transcript`: Text. Avg 1,191 chars, range 992-1,428. Short enough to embed whole.
- `sentiment`: String(20). 4 values.
- `agent_name`: String(50). 10 unique agents.

**Indexes**:
- Primary key on `id`
- Unique index on `ticket_id`
- Index on `channel`
- Index on `sentiment`

#### `backend/vector_db/models/question.py`

```python
class AnswerType(StrEnum):
    SCRIPT = "SCRIPT"
    KB = "KB"
    TICKET_RESOLUTION = "TICKET_RESOLUTION"

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str]              # PK, e.g. "Q-0001"
    question_text: Mapped[str]   # The question (Text column)
    answer_type: Mapped[str]     # SCRIPT | KB | TICKET_RESOLUTION
    target_id: Mapped[str]       # Polymorphic FK (SCRIPT-xxx, KB-xxx, or CS-xxx)
    category: Mapped[str]        # e.g. "Certifications"
    module: Mapped[str]          # e.g. "Compliance / Certifications"
    source: Mapped[str]          # "Scripts" or "AFF Data"
    difficulty: Mapped[str | None]  # e.g. "Medium"
    embedding: Mapped[...]       # pgvector Vector(1536), nullable
```

**Column details from dataset**:
- `id`: String(10). Format `Q-{0001-1000}`. 1,000 rows.
- `question_text`: Text. Avg ~200 chars.
- `answer_type`: String(30). SCRIPT (70%), KB (21%), TICKET_RESOLUTION (9%).
- `target_id`: String(20). Polymorphic: points to scripts, KB articles, or tickets depending on answer_type.
- `category`: String(100). 14 unique values.
- `source`: String(20). "Scripts" (70%) or "AFF Data" (30%).

**Note**: The `target_id` is intentionally polymorphic (not a real FK) — the `answer_type` determines which table it points to. This matches the dataset design.

**Indexes**:
- Primary key on `id`
- Index on `answer_type`
- Index on `category`
- IVFFlat index on `embedding` with `lists=32`

#### `backend/vector_db/models/kb_lineage.py`

```python
class LineageSourceType(StrEnum):
    TICKET = "TICKET"
    CONVERSATION = "CONVERSATION"
    SCRIPT = "SCRIPT"

class LineageRelationship(StrEnum):
    CREATED_FROM = "CREATED_FROM"
    REFERENCES = "REFERENCES"

class KBLineage(Base):
    __tablename__ = "kb_lineage"

    id: Mapped[str]              # PK, auto-generated UUID
    kb_article_id: Mapped[str]   # FK to knowledge_articles
    source_type: Mapped[str]     # TICKET | CONVERSATION | SCRIPT
    source_id: Mapped[str]       # Polymorphic: ticket_id, conversation_id, or script_id
    relationship: Mapped[str]    # CREATED_FROM | REFERENCES
    created_at: Mapped[datetime]
```

**Column details from dataset**:
- 483 rows. Each synthetic KB article has exactly 3 lineage records (1 ticket + 1 conversation + 1 script).
- `source_type`: Equal distribution — 161 TICKET, 161 CONVERSATION, 161 SCRIPT.
- `relationship`: CREATED_FROM (322 rows, for ticket+conversation) or REFERENCES (161 rows, for script).

**Indexes**:
- Primary key on `id`
- Index on `kb_article_id` (lookup provenance for an article)
- Index on `source_id` (reverse lookup: what articles came from this ticket?)

#### `backend/vector_db/models/learning_event.py`

```python
class LearningEventStatus(StrEnum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[str]                        # PK, e.g. "LEARN-0001"
    trigger_ticket_id: Mapped[str]         # FK to tickets
    detected_gap: Mapped[str]              # Description of the knowledge gap (Text)
    proposed_kb_article_id: Mapped[str | None]  # FK to knowledge_articles (the draft)
    status: Mapped[str]                    # Pending | Approved | Rejected
    reviewer_role: Mapped[str | None]      # e.g. "Tier 3 Support", "Support Ops Review"
    reviewed_at: Mapped[datetime | None]
    created_at: Mapped[datetime]
```

**Column details from dataset**:
- 161 rows. 134 Approved, 27 Rejected, 0 Pending in seed data.
- `detected_gap`: Text. Describes what's missing, e.g. "No existing KB match above threshold for Advance Property Date issue; escalated to Tier 3."
- `reviewer_role`: String(50). "Tier 3 Support" or "Support Ops Review".

**Indexes**:
- Primary key on `id`
- Index on `status` (filter pending reviews)
- Index on `trigger_ticket_id`
- Index on `proposed_kb_article_id`

#### `backend/vector_db/models/placeholder.py`

```python
class Placeholder(Base):
    __tablename__ = "placeholders"

    id: Mapped[str]              # PK, auto-generated UUID
    token: Mapped[str]           # e.g. "<LEASE_ID>"  (unique)
    meaning: Mapped[str]         # Human description
    example: Mapped[str]         # Usage example
```

**Column details from dataset**:
- 25 rows. Static reference data.
- `token`: String(50). Unique.

### 3.2 Model Registration

Update `backend/vector_db/models/__init__.py`:

```python
from vector_db.models.user import User
from vector_db.models.knowledge_article import KnowledgeArticle
from vector_db.models.script import Script
from vector_db.models.ticket import Ticket
from vector_db.models.conversation import Conversation
from vector_db.models.question import Question
from vector_db.models.kb_lineage import KBLineage
from vector_db.models.learning_event import LearningEvent
from vector_db.models.placeholder import Placeholder

__all__ = [
    "User",
    "KnowledgeArticle",
    "Script",
    "Ticket",
    "Conversation",
    "Question",
    "KBLineage",
    "LearningEvent",
    "Placeholder",
]
```

### 3.3 pgvector Setup

The pgvector extension must be enabled before creating tables. Add to the lifespan in `api/main.py` (before `Base.metadata.create_all`):

```python
from sqlalchemy import text

async with engine.begin() as conn:
    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    await conn.run_sync(Base.metadata.create_all)
```

### 3.4 IVFFlat Index Creation

IVFFlat indexes should be created **after** data import (they need data to build the index). Create a script `backend/scripts/create_vector_indexes.py`:

```sql
-- Run after data import and embedding generation
CREATE INDEX IF NOT EXISTS idx_kb_articles_embedding
    ON knowledge_articles USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 80);

CREATE INDEX IF NOT EXISTS idx_scripts_embedding
    ON scripts USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 27);

CREATE INDEX IF NOT EXISTS idx_questions_embedding
    ON questions USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 32);
```

Formula: `lists = max(1, sqrt(num_rows))`. KB: sqrt(3207)=57 → round up to 80. Scripts: sqrt(714)=27. Questions: sqrt(1000)=32.

---

## 4. Backend API Team

### 4.1 New Route Modules

All routes go in `backend/api/v1/`. Follow the existing pattern from `users.py`: Pydantic request/response schemas, async handlers, dependency injection for auth and DB.

#### Route Registration

Update `backend/api/v1/__init__.py`:

```python
from api.v1 import auth, chat, users, copilot, knowledge, learning, dashboard

router.include_router(copilot.router, prefix="/copilot", tags=["copilot"])
router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
router.include_router(learning.router, prefix="/learning", tags=["learning"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
```

---

#### `backend/api/v1/copilot.py` — Triage Copilot

**POST `/api/v1/copilot/ask`** — Main triage endpoint

Request:
```json
{
    "question": "Date advance fails because a backend voucher reference is invalid..."
}
```

Response:
```json
{
    "classification": {
        "answer_type": "SCRIPT",
        "confidence": 0.92,
        "reasoning": "Question describes a backend data fix scenario requiring Tier 3 script"
    },
    "results": [
        {
            "rank": 1,
            "source_type": "SCRIPT",
            "source_id": "SCRIPT-0293",
            "title": "Accounting / Date Advance - Advance Property Date",
            "content_preview": "use <DATABASE>\ngo\n-- <SITE_NAME>...",
            "similarity_score": 0.94,
            "category": "Advance Property Date",
            "placeholders": ["<DATABASE>", "<SITE_NAME>", "<ID>"],
            "provenance": null
        },
        {
            "rank": 2,
            "source_type": "KB",
            "source_id": "KB-SYN-0042",
            "title": "Resolving Date Advance Backend Data Sync Issues",
            "content_preview": "When a date advance fails due to...",
            "similarity_score": 0.87,
            "category": "Advance Property Date",
            "placeholders": null,
            "provenance": {
                "created_from_ticket": "CS-38908386",
                "created_from_conversation": "CONV-O2RAK1VRJN",
                "references_script": "SCRIPT-0293"
            }
        }
    ],
    "metadata": {
        "search_time_ms": 45,
        "total_candidates": 3207,
        "model_used": "gpt-5"
    }
}
```

Pydantic schemas:

```python
class CopilotAskRequest(BaseModel):
    question: str

class Classification(BaseModel):
    answer_type: str          # SCRIPT | KB | TICKET_RESOLUTION
    confidence: float
    reasoning: str

class ProvenanceInfo(BaseModel):
    created_from_ticket: str | None = None
    created_from_conversation: str | None = None
    references_script: str | None = None

class SearchResult(BaseModel):
    rank: int
    source_type: str
    source_id: str
    title: str
    content_preview: str      # First 500 chars
    similarity_score: float
    category: str | None
    placeholders: list[str] | None = None  # For scripts only
    provenance: ProvenanceInfo | None = None  # For synth KB only

class CopilotAskResponse(BaseModel):
    classification: Classification
    results: list[SearchResult]
    metadata: dict[str, Any]
```

**Implementation logic**:
1. Call `TriageAgent` to classify the question → get `answer_type`
2. Embed the question using `EmbeddingService`
3. Run vector similarity search against the classified pool (scripts, KB articles, or tickets)
4. Also search secondary pools for supplementary results
5. For each KB result with `source_type=SYNTH_FROM_TICKET`, fetch provenance from `kb_lineage`
6. For each script result, extract placeholder tokens from the text
7. Return top-5 results ranked by similarity

---

**GET `/api/v1/copilot/evaluate`** — Run accuracy evaluation against ground truth

Response:
```json
{
    "total_questions": 1000,
    "classification_accuracy": 0.89,
    "retrieval_accuracy": {
        "hit_at_1": 0.72,
        "hit_at_3": 0.85,
        "hit_at_5": 0.91
    },
    "by_answer_type": {
        "SCRIPT": { "count": 700, "hit_at_1": 0.75, "hit_at_3": 0.88 },
        "KB": { "count": 209, "hit_at_1": 0.68, "hit_at_3": 0.82 },
        "TICKET_RESOLUTION": { "count": 91, "hit_at_1": 0.61, "hit_at_3": 0.76 }
    },
    "evaluated_at": "2026-02-07T15:30:00Z"
}
```

**Implementation logic**:
1. Iterate through all questions in DB
2. For each: embed question → search the appropriate pool → check if `target_id` appears in top-k results
3. Aggregate accuracy metrics
4. This is an admin-only, long-running endpoint. Consider running async and caching results.

---

#### `backend/api/v1/knowledge.py` — Knowledge Base

**GET `/api/v1/knowledge/`** — List/search KB articles

Query params:
- `search` (optional): Text search / filter
- `source_type` (optional): `SEED_KB` | `SYNTH_FROM_TICKET`
- `category` (optional): Filter by category
- `status` (optional): `Active` | `Draft` | `Archived`
- `page` (default 1), `page_size` (default 20)

Response:
```json
{
    "items": [
        {
            "id": "KB-SYN-0001",
            "title": "Resolving Date Advance Backend Data Sync Issues",
            "source_type": "SYNTH_FROM_TICKET",
            "status": "Active",
            "category": "Advance Property Date",
            "created_at": "2025-02-17T10:00:00Z",
            "version": 1,
            "body_preview": "When a date advance fails..."
        }
    ],
    "total": 3207,
    "page": 1,
    "page_size": 20
}
```

**GET `/api/v1/knowledge/{article_id}`** — Article detail + lineage

Response:
```json
{
    "id": "KB-SYN-0001",
    "title": "Resolving Date Advance Backend Data Sync Issues",
    "body": "Full article text...",
    "source_type": "SYNTH_FROM_TICKET",
    "status": "Active",
    "category": "Advance Property Date",
    "version": 1,
    "created_at": "2025-02-17T10:00:00Z",
    "updated_at": "2025-02-17T10:00:00Z",
    "lineage": [
        {
            "source_type": "TICKET",
            "source_id": "CS-38908386",
            "relationship": "CREATED_FROM",
            "source_summary": "Unable to advance property date (backend data sync)"
        },
        {
            "source_type": "CONVERSATION",
            "source_id": "CONV-O2RAK1VRJN",
            "relationship": "CREATED_FROM",
            "source_summary": "Chat with Alex — Accounting Clerk at Oak & Ivy Management"
        },
        {
            "source_type": "SCRIPT",
            "source_id": "SCRIPT-0293",
            "relationship": "REFERENCES",
            "source_summary": "Accounting / Date Advance - Advance Property Date"
        }
    ]
}
```

**Implementation logic**:
- List endpoint: Standard paginated query with filters. For text search, use `ILIKE` on title/body (or vector search if search term is long).
- Detail endpoint: Fetch article + LEFT JOIN kb_lineage + lookup source summaries from tickets/conversations/scripts.

---

#### `backend/api/v1/learning.py` — Learning Loop

**GET `/api/v1/learning/events`** — List learning events

Query params:
- `status` (optional): `Pending` | `Approved` | `Rejected`
- `page`, `page_size`

Response:
```json
{
    "items": [
        {
            "id": "LEARN-0001",
            "trigger_ticket_id": "CS-38908386",
            "trigger_ticket_subject": "Unable to advance property date",
            "detected_gap": "No existing KB match above threshold...",
            "proposed_kb_article_id": "KB-SYN-0001",
            "proposed_kb_title": "Resolving Date Advance Backend Data Sync Issues",
            "status": "Approved",
            "reviewer_role": "Tier 3 Support",
            "reviewed_at": "2025-02-17T12:00:00Z",
            "created_at": "2025-02-17T10:00:00Z"
        }
    ],
    "total": 161,
    "page": 1,
    "page_size": 20
}
```

**POST `/api/v1/learning/detect-gap`** — Trigger gap detection for a ticket

Request:
```json
{
    "ticket_id": "CS-38908386"
}
```

Response:
```json
{
    "gap_detected": true,
    "learning_event_id": "LEARN-NEW-001",
    "detected_gap": "No existing KB match above 0.85 threshold...",
    "proposed_article": {
        "id": "KB-SYN-NEW-001",
        "title": "Auto-generated: Resolving Date Advance...",
        "body": "Generated article content...",
        "status": "Draft"
    }
}
```

**Implementation logic**:
1. Fetch the ticket + its conversation + its script (if any)
2. Embed the ticket description + resolution
3. Search existing KB for a match above similarity threshold (0.85)
4. If no match → call `GapDetectionAgent` to confirm the gap
5. Call `KBGenerationAgent` to generate a draft article
6. Save the draft KB article (status=Draft, source_type=SYNTH_FROM_TICKET)
7. Create lineage records linking the new article to ticket + conversation + script
8. Create a learning event (status=Pending)
9. Return the event

**POST `/api/v1/learning/review/{event_id}`** — Approve or reject a learning event

Request:
```json
{
    "decision": "Approved",
    "reviewer_role": "Tier 3 Support"
}
```

Response:
```json
{
    "id": "LEARN-0001",
    "status": "Approved",
    "reviewed_at": "2026-02-07T15:30:00Z",
    "kb_article_status": "Active"
}
```

**Implementation logic**:
1. Update learning event status
2. If approved: set proposed KB article status to `Active`, generate embedding, make it searchable
3. If rejected: set proposed KB article status to `Archived`

---

#### `backend/api/v1/dashboard.py` — Metrics Dashboard

**GET `/api/v1/dashboard/metrics`** — Aggregated metrics

Response:
```json
{
    "knowledge_base": {
        "total_articles": 3207,
        "seed_articles": 3046,
        "synth_articles": 161,
        "active_articles": 3180,
        "draft_articles": 5,
        "articles_with_embeddings": 3200,
        "categories": [
            { "name": "General", "count": 1200 },
            { "name": "Advance Property Date", "count": 450 }
        ]
    },
    "learning": {
        "total_events": 161,
        "approved": 134,
        "rejected": 27,
        "pending": 0,
        "approval_rate": 0.83
    },
    "tickets": {
        "total": 400,
        "by_tier": { "1": 120, "2": 119, "3": 161 },
        "by_priority": { "Low": 67, "Medium": 146, "High": 137, "Critical": 50 },
        "by_root_cause": {
            "Data inconsistency requiring backend fix": 161,
            "Knowledge gap / workflow guidance": 121,
            "Configuration / setup": 118
        }
    },
    "scripts": {
        "total": 714,
        "by_category": [
            { "name": "Certifications", "count": 250 },
            { "name": "Advance Property Date", "count": 200 }
        ]
    }
}
```

**Implementation logic**: Straightforward aggregate queries with `func.count()`, `GROUP BY`, etc.

---

### 4.2 Pydantic Schema Files

Create `backend/api/v1/schemas/` directory with:

```
backend/api/v1/schemas/
├── __init__.py
├── copilot.py      # CopilotAskRequest, CopilotAskResponse, etc.
├── knowledge.py    # KBArticleListResponse, KBArticleDetailResponse, etc.
├── learning.py     # LearningEventResponse, DetectGapRequest, ReviewRequest, etc.
└── dashboard.py    # DashboardMetricsResponse
```

This keeps schemas separate from route logic, following a clean architecture pattern.

---

## 5. AI Agents Team

### 5.1 Overview

All agents extend `BaseAgent` from `backend/agents/base.py`. Each agent uses OpenAI GPT-5 for LLM calls and `EmbeddingService` for vector operations.

```
backend/agents/
├── base.py            # Existing abstract base class
├── triage.py          # TriageAgent — classify + retrieve
├── gap_detection.py   # GapDetectionAgent — detect knowledge gaps
├── kb_generation.py   # KBGenerationAgent — generate KB articles
└── qa_scoring.py      # QAScoringAgent — score interaction quality (stretch)
```

### 5.2 Vector Search Service

Before building agents, create a reusable vector search service.

**File**: `backend/vector_db/search.py`

```python
class VectorSearchService:
    """Semantic search over pgvector-indexed tables."""

    async def search_knowledge_articles(
        self,
        query_embedding: list[float],
        limit: int = 5,
        status_filter: str = "Active",
        category_filter: str | None = None,
    ) -> list[dict]:
        """Search KB articles by cosine similarity."""
        # Uses: SELECT *, 1 - (embedding <=> :query) as similarity
        #       FROM knowledge_articles
        #       WHERE status = :status AND embedding IS NOT NULL
        #       ORDER BY embedding <=> :query
        #       LIMIT :limit

    async def search_scripts(
        self,
        query_embedding: list[float],
        limit: int = 5,
        category_filter: str | None = None,
    ) -> list[dict]:
        """Search scripts by cosine similarity."""

    async def search_tickets(
        self,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[dict]:
        """Search tickets by embedding on resolution text."""
        # Note: Tickets don't have embeddings in the schema above.
        # For ticket search, embed the resolution field at query time
        # OR add an embedding column to tickets.
        # Decision: For simplicity, search tickets by embedding their
        # description+resolution at import time. Add embedding column to Ticket model.

    async def search_all(
        self,
        query_embedding: list[float],
        answer_type: str,
        limit: int = 5,
    ) -> list[dict]:
        """Search the pool matching the classified answer_type."""
        if answer_type == "SCRIPT":
            return await self.search_scripts(query_embedding, limit)
        elif answer_type == "KB":
            return await self.search_knowledge_articles(query_embedding, limit)
        elif answer_type == "TICKET_RESOLUTION":
            return await self.search_tickets(query_embedding, limit)
```

**Implementation notes**:
- Use `sqlalchemy.text()` for the pgvector `<=>` cosine distance operator.
- Return dicts with `id`, `title`, `content_preview`, `similarity_score`, `category`.
- Accept an `AsyncSession` as parameter (injected from route).

---

### 5.3 TriageAgent

**File**: `backend/agents/triage.py`

**Purpose**: Given a support question, classify its answer_type (SCRIPT/KB/TICKET_RESOLUTION) and retrieve the best matching resources.

**Input**: `AgentMessage` with the user's question.

**Processing**:

1. **Classification** via LLM (GPT-5):
   ```
   System prompt:
   You are a support triage classifier for ExampleCo PropertySuite Affordable.
   Given a customer support question, classify what type of resource would best answer it.

   Categories:
   - SCRIPT: The question describes a backend data issue that requires a SQL fix script.
     Indicators: "backend data", "sync", "invalid reference", "Tier 3", data fix needed.
   - KB: The question asks about a workflow, how-to, configuration, or best practice.
     Indicators: "how to", "where do I", "steps to", general guidance needed.
   - TICKET_RESOLUTION: The question asks about how a specific past issue was resolved.
     Indicators: references a specific scenario, asks for precedent, resolution steps.

   Respond with JSON: {"answer_type": "SCRIPT|KB|TICKET_RESOLUTION", "confidence": 0.0-1.0, "reasoning": "..."}
   ```
2. **Embedding**: Embed the question text.
3. **Retrieval**: Call `VectorSearchService.search_all()` with the classified type.
4. **Secondary search**: Also search other pools with lower weight for supplementary results.

**Output**: `AgentResponse` with content as JSON (classification + ranked results), metadata includes search_time_ms.

---

### 5.4 GapDetectionAgent

**File**: `backend/agents/gap_detection.py`

**Purpose**: Given a resolved ticket, determine if the resolution represents new knowledge not captured in the existing KB.

**Input**: `AgentMessage` containing the ticket data (description, resolution, category, root_cause) + conversation transcript.

**Processing**:

1. **Embed** the ticket's resolution text.
2. **Search** existing KB articles for similarity. If best match is above threshold (0.85) → no gap.
3. If below threshold, **confirm via LLM**:
   ```
   System prompt:
   You are a knowledge gap detector. You are given a resolved support ticket and
   the closest matching existing KB article.

   Determine if the ticket resolution contains NEW knowledge that should be captured
   in a KB article. Consider:
   - Does the existing KB cover this scenario?
   - Is the resolution substantially different from existing articles?
   - Would a new article help future agents?

   Respond with JSON: {"gap_detected": true/false, "gap_description": "...", "suggested_title": "..."}
   ```

**Output**: `AgentResponse` with gap detection result.

---

### 5.5 KBGenerationAgent

**File**: `backend/agents/kb_generation.py`

**Purpose**: Generate a draft KB article from a ticket + conversation + script.

**Input**: `AgentMessage` containing the full ticket, conversation transcript, and script text (if applicable).

**Processing**:

1. **Generate article via LLM**:
   ```
   System prompt:
   You are a technical writer for ExampleCo PropertySuite Affordable support.
   Generate a knowledge base article from the provided resolved support ticket.

   Requirements:
   - Title: Clear, searchable title describing the issue and resolution
   - Body structure:
     1. Problem description (what the user experiences)
     2. Root cause (why it happens)
     3. Resolution steps (numbered, actionable)
     4. Related information (category, module, affected roles)
   - Use the conversation transcript for context on the user's experience
   - If a Tier 3 script was used, reference it but don't include raw SQL
   - Keep the language professional and consistent with existing KB articles
   - Use placeholders from the placeholder dictionary where appropriate

   Respond with JSON: {"title": "...", "body": "...", "category": "..."}
   ```

**Output**: `AgentResponse` with the generated article content.

---

### 5.6 QAScoringAgent (Stretch Goal)

**File**: `backend/agents/qa_scoring.py`

**Purpose**: Score a conversation transcript using the QA rubric from the dataset.

The `QA_Evaluation_Prompt` tab in the dataset contains a detailed rubric. Use it as the system prompt for an LLM evaluator.

This is a **stretch goal** — implement only if time permits.

---

## 6. Frontend Team

### 6.1 Overview

All new pages are protected routes. Follow the existing dashboard page pattern: `ProtectedRoute` wrapper, card-based layout, teal/cyan accent colors on dark background.

### 6.2 Navigation

Add a sidebar or top navigation that replaces the current minimal nav. Pages:

| Route | Label | Icon (Lucide) |
|-------|-------|---------------|
| `/dashboard` | Dashboard | `LayoutDashboard` |
| `/copilot` | Copilot | `MessageSquareText` |
| `/knowledge` | Knowledge Base | `BookOpen` |
| `/knowledge/[id]` | Article Detail | — |
| `/learning` | Learning Feed | `Brain` |

Create a shared layout component `frontend/web/src/components/layout/app-layout.tsx` that wraps all authenticated pages with consistent nav + sidebar.

### 6.3 API Client Extensions

Add to `frontend/web/src/lib/api.ts`:

```typescript
// --- Types ---

interface Classification {
  answer_type: string;
  confidence: number;
  reasoning: string;
}

interface ProvenanceInfo {
  created_from_ticket: string | null;
  created_from_conversation: string | null;
  references_script: string | null;
}

interface SearchResult {
  rank: number;
  source_type: string;
  source_id: string;
  title: string;
  content_preview: string;
  similarity_score: number;
  category: string | null;
  placeholders: string[] | null;
  provenance: ProvenanceInfo | null;
}

interface CopilotResponse {
  classification: Classification;
  results: SearchResult[];
  metadata: Record<string, any>;
}

interface KBArticleListItem {
  id: string;
  title: string;
  source_type: string;
  status: string;
  category: string | null;
  created_at: string;
  version: number;
  body_preview: string;
}

interface KBArticleDetail {
  id: string;
  title: string;
  body: string;
  source_type: string;
  status: string;
  category: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  lineage: LineageEntry[];
}

interface LineageEntry {
  source_type: string;
  source_id: string;
  relationship: string;
  source_summary: string;
}

interface LearningEvent {
  id: string;
  trigger_ticket_id: string;
  trigger_ticket_subject: string;
  detected_gap: string;
  proposed_kb_article_id: string | null;
  proposed_kb_title: string | null;
  status: string;
  reviewer_role: string | null;
  reviewed_at: string | null;
  created_at: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

interface DashboardMetrics {
  knowledge_base: { ... };
  learning: { ... };
  tickets: { ... };
  scripts: { ... };
}

// --- API Methods ---

export const api = {
  // ... existing methods (login, register, getMe) ...

  // Copilot
  copilotAsk: (question: string) =>
    request<CopilotResponse>('/api/v1/copilot/ask', {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

  // Knowledge Base
  listKBArticles: (params?: {
    search?: string;
    source_type?: string;
    category?: string;
    status?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined) query.set(k, String(v));
      });
    }
    return request<PaginatedResponse<KBArticleListItem>>(
      `/api/v1/knowledge/?${query}`
    );
  },

  getKBArticle: (id: string) =>
    request<KBArticleDetail>(`/api/v1/knowledge/${id}`),

  // Learning
  listLearningEvents: (params?: { status?: string; page?: number }) => {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined) query.set(k, String(v));
      });
    }
    return request<PaginatedResponse<LearningEvent>>(
      `/api/v1/learning/events?${query}`
    );
  },

  detectGap: (ticketId: string) =>
    request<any>('/api/v1/learning/detect-gap', {
      method: 'POST',
      body: JSON.stringify({ ticket_id: ticketId }),
    }),

  reviewLearningEvent: (eventId: string, decision: string, reviewerRole: string) =>
    request<any>(`/api/v1/learning/review/${eventId}`, {
      method: 'POST',
      body: JSON.stringify({ decision, reviewer_role: reviewerRole }),
    }),

  // Dashboard
  getDashboardMetrics: () =>
    request<DashboardMetrics>('/api/v1/dashboard/metrics'),
};
```

### 6.4 Page Specifications

#### Page 1: Copilot (`/copilot`)

**Layout**: Full-width. Large text area at top, results below.

**Components**:
- **Search bar**: Large `<textarea>` with "Ask a question..." placeholder and Submit button
- **Classification badge**: After response, show a colored badge: SCRIPT (purple), KB (blue), TICKET_RESOLUTION (amber) + confidence percentage
- **Results list**: Cards for each result
  - Card shows: rank, title, source_type badge, similarity score (as percentage bar), category tag
  - Expandable: click to see `content_preview`
  - For scripts: show placeholder tokens as small badges (e.g. `<DATABASE>`, `<SITE_NAME>`)
  - For synth KB: show provenance chain as linked breadcrumb (Ticket → Conversation → Script)
- **Loading state**: Animated skeleton cards while searching

**Interactions**:
1. User types/pastes question → clicks Submit (or Ctrl+Enter)
2. System shows loading spinner with "Classifying and searching..."
3. Results appear with classification badge and ranked results
4. Click on a result to expand the full content
5. Click on a source_id link to navigate to the detail page (KB article or script)

#### Page 2: Knowledge Base (`/knowledge`)

**Layout**: Sidebar filters + main content area.

**Components**:
- **Filter sidebar**:
  - Source type toggle: All | Seed KB | Auto-generated
  - Category dropdown (14 categories from dataset)
  - Status filter: Active | Draft | Archived
  - Text search input
- **Article list**: Card grid or table. Each row: title, source_type badge, category, created_at, version
- **Pagination**: Page navigation at bottom

**Interactions**:
1. Filters update the list via API query params
2. Click article → navigate to `/knowledge/[id]`
3. Source type "Auto-generated" badge shows a sparkle icon to distinguish AI-created content

#### Page 3: Article Detail (`/knowledge/[id]`)

**Layout**: Full-width article view.

**Components**:
- **Article header**: Title, source_type badge, status badge, category, version, timestamps
- **Article body**: Rendered as formatted text (preserve line breaks)
- **Provenance section** (for synth articles only): Visual chain showing:
  ```
  Ticket CS-38908386 → Conversation CONV-O2RAK1VRJN → Script SCRIPT-0293
  ```
  Each node is clickable (shows a modal or navigates to detail)
- **Version history** (stretch): Timeline of changes

#### Page 4: Learning Feed (`/learning`)

**Layout**: Timeline / feed style.

**Components**:
- **Status filter tabs**: All | Pending | Approved | Rejected
- **Event cards**: Each card shows:
  - Status badge (Pending=yellow, Approved=green, Rejected=red)
  - Trigger ticket subject + link
  - Detected gap description
  - Proposed article title + link
  - Reviewer role + review date (if reviewed)
- **Review actions** (for Pending events): Approve / Reject buttons → opens confirmation modal
- **Pending count badge** on the tab and in nav

**Interactions**:
1. Filter by status
2. Click "Approve" → confirmation modal → POST review → update card status
3. Click ticket link → modal showing ticket details
4. Click article link → navigate to `/knowledge/[id]`

#### Page 5: Dashboard (`/dashboard`) — Redesign existing

**Layout**: Metric cards + charts.

**Components**:
- **Top row — Summary cards** (4 cards):
  - Total KB Articles (with seed vs synth breakdown)
  - Total Scripts
  - Learning Events (with pending count highlighted)
  - Approval Rate (as percentage)
- **Middle row — Charts**:
  - KB articles by category (bar chart)
  - Tickets by priority (donut chart)
  - Tickets by root cause (donut chart)
  - Learning events over time (line chart, if timestamps available)
- **Bottom row — Tables**:
  - Recent learning events (last 10)
  - Top categories by ticket volume

**Note**: Charts can use a lightweight library. Options:
- `recharts` (React-native, most popular)
- Raw SVG (minimal dependency)
- Install: `pnpm add recharts`

### 6.5 New Frontend Dependencies

```bash
cd frontend/web
COREPACK_INTEGRITY_KEYS=0 pnpm add recharts
COREPACK_INTEGRITY_KEYS=0 pnpm dlx shadcn@latest add badge tabs textarea separator skeleton scroll-area
```

### 6.6 File Structure

```
frontend/web/src/
├── app/
│   ├── layout.tsx              # Existing — unchanged
│   ├── providers.tsx           # Existing — unchanged
│   ├── page.tsx                # Existing landing page
│   ├── login/page.tsx          # Existing
│   ├── register/page.tsx       # Existing
│   ├── dashboard/page.tsx      # MODIFY — new metrics dashboard
│   ├── copilot/page.tsx        # NEW — triage copilot
│   ├── knowledge/
│   │   ├── page.tsx            # NEW — KB article list
│   │   └── [id]/page.tsx       # NEW — KB article detail
│   └── learning/page.tsx       # NEW — learning feed
├── components/
│   ├── auth/
│   │   └── protected-route.tsx # Existing
│   ├── layout/
│   │   └── app-layout.tsx      # NEW — shared nav + sidebar
│   ├── copilot/
│   │   ├── search-bar.tsx      # NEW — question input
│   │   ├── classification-badge.tsx  # NEW
│   │   └── result-card.tsx     # NEW
│   ├── knowledge/
│   │   ├── article-card.tsx    # NEW
│   │   ├── article-filters.tsx # NEW
│   │   └── provenance-chain.tsx # NEW
│   ├── learning/
│   │   ├── event-card.tsx      # NEW
│   │   └── review-modal.tsx    # NEW
│   ├── dashboard/
│   │   ├── metric-card.tsx     # NEW
│   │   └── category-chart.tsx  # NEW
│   └── ui/                     # Existing shadcn components
├── contexts/
│   └── auth-context.tsx        # Existing
└── lib/
    ├── api.ts                  # MODIFY — add new API methods
    └── utils.ts                # Existing
```

---

## 7. Data Import Pipeline

### 7.1 Import Script

**File**: `backend/scripts/import_data.py`

A CLI script that reads the Excel workbook and populates the database.

**Steps**:
1. Read each sheet using `openpyxl` or `pandas`
2. Insert rows into corresponding tables in dependency order:
   - `placeholders` (no FK deps)
   - `knowledge_articles` (from both `Knowledge_Articles` and `Existing_Knowledge_Articles` sheets)
   - `scripts` (from `Scripts_Master`)
   - `tickets` (FK to knowledge_articles and scripts)
   - `conversations` (FK to tickets)
   - `questions` (polymorphic target_id — no real FK)
   - `kb_lineage` (FK to knowledge_articles)
   - `learning_events` (FK to tickets and knowledge_articles)
3. Deduplicate knowledge articles (the `Knowledge_Articles` sheet includes 3,046 from `Existing_Knowledge_Articles` + 161 synthetic = 3,207 total; `Existing_Knowledge_Articles` is a subset)

**Deduplication strategy**: Use the `Knowledge_Articles` sheet as the source of truth (it contains all 3,207 articles). Ignore `Existing_Knowledge_Articles` — it's a subset.

### 7.2 Embedding Generation Script

**File**: `backend/scripts/generate_embeddings.py`

A CLI script that generates embeddings for all embeddable content.

**Steps**:
1. Fetch all KB articles without embeddings
2. For each article: embed `title + "\n" + body` (concatenated)
3. Batch process (OpenAI supports batches of up to 2048 texts)
4. Update the `embedding` column
5. Repeat for scripts (embed `title + "\n" + script_text`)
6. Repeat for questions (embed `question_text`)

**Estimated cost**: ~6,000 texts * ~500 tokens avg = ~3M tokens. At $0.02/1M tokens for text-embedding-3-small = **~$0.06 total**.

**Batch strategy**: Process in batches of 100 to avoid rate limits. Estimated time: ~2 minutes.

### 7.3 Makefile Targets

```makefile
# ─── Data ──────────────────────────────────────────────────

import-data:
	cd backend && uv run python -m scripts.import_data

generate-embeddings:
	cd backend && uv run python -m scripts.generate_embeddings

create-vector-indexes:
	cd backend && uv run python -m scripts.create_vector_indexes

seed: import-data generate-embeddings create-vector-indexes
```

### 7.4 Adding Dependencies

Add `openpyxl` to `backend/pyproject.toml`:

```toml
dependencies = [
    # ... existing deps ...
    "openpyxl>=3.1.0",
]
```

Then run `cd backend && uv sync`.

---

## 8. Integration Points & Contracts

### 8.1 Agent ↔ API Integration

The API layer calls agents as services. Each agent is instantiated and called with `await agent.run(messages)`.

```python
# In copilot.py route handler
from agents.triage import TriageAgent

agent = TriageAgent(db=db, embedding_service=embedding_service, search_service=search_service)
response = await agent.run([AgentMessage(role="user", content=request.question)])
```

Agents receive a DB session and services as constructor parameters (not through FastAPI Depends — agents aren't routes).

### 8.2 Frontend ↔ Backend Contract

The API contract (request/response JSON shapes) is defined in Section 4 above. Both teams should work against these contracts. If the backend isn't ready, the frontend can mock responses using local JSON files.

### 8.3 Shared Constants

Create `backend/api/core/constants.py` for shared enums and constants:

```python
# Similarity thresholds
KB_GAP_THRESHOLD = 0.85           # Below this = gap detected
SEARCH_RESULT_LIMIT = 5           # Default top-k results
CONTENT_PREVIEW_LENGTH = 500      # Chars to show in previews

# Embedding config
EMBEDDING_TEXT_SEPARATOR = "\n"   # Separator for title+body concatenation
```

---

## 9. Development Order & Dependencies

### Phase 1: Foundation (All teams, parallel)

| Team | Task | Depends On |
|------|------|------------|
| Database | Create all model files | Nothing |
| Database | Update `__init__.py` model registration | Model files |
| Database | Add pgvector extension to lifespan | Nothing |
| Backend | Create `schemas/` directory + all Pydantic schemas | API contracts in this doc |
| Backend | Create stub route files (return mock data) | Schemas |
| AI Agents | Create `VectorSearchService` | Model files |
| AI Agents | Create `TriageAgent` skeleton | BaseAgent |
| Frontend | Create `app-layout.tsx` shared navigation | Nothing |
| Frontend | Extend `api.ts` with new types + methods | API contracts in this doc |
| Frontend | Create all page files with placeholder UI | API types |

**Milestone**: `make dev` starts cleanly. All routes return mock data. Frontend pages render with placeholder content.

### Phase 2: Data Pipeline (Database team)

| Task | Depends On |
|------|------------|
| Write `import_data.py` script | Model files + pgvector |
| Import Excel data into PostgreSQL | import_data.py |
| Write `generate_embeddings.py` script | Import complete |
| Generate embeddings for all content | generate_embeddings.py |
| Create IVFFlat indexes | Embeddings generated |
| Add Makefile targets (`seed`, etc.) | Scripts complete |

**Milestone**: `make seed` imports all data + generates embeddings + creates indexes. Database has 3,207 KB articles, 714 scripts, 400 tickets, etc., all with vector embeddings.

### Phase 3: Core Features (Backend + Agents, parallel)

| Team | Task | Depends On |
|------|------|------------|
| AI Agents | Implement `VectorSearchService` with real pgvector queries | Phase 2 (data in DB) |
| AI Agents | Implement `TriageAgent` with LLM classification + vector search | VectorSearchService |
| AI Agents | Implement `GapDetectionAgent` | VectorSearchService |
| AI Agents | Implement `KBGenerationAgent` | GapDetectionAgent |
| Backend | Implement `/copilot/ask` with TriageAgent | TriageAgent |
| Backend | Implement `/knowledge/` list + detail endpoints | Phase 2 (data in DB) |
| Backend | Implement `/learning/events` list endpoint | Phase 2 |
| Backend | Implement `/learning/detect-gap` endpoint | GapDetectionAgent + KBGenerationAgent |
| Backend | Implement `/learning/review/{id}` endpoint | Phase 2 |
| Backend | Implement `/dashboard/metrics` endpoint | Phase 2 |
| Backend | Implement `/copilot/evaluate` endpoint | TriageAgent + Phase 2 |

**Milestone**: All API endpoints return real data. Copilot classifies and retrieves correctly. Gap detection generates draft articles.

### Phase 4: Frontend Integration (Frontend team)

| Task | Depends On |
|------|------------|
| Connect Copilot page to `/copilot/ask` endpoint | Phase 3 endpoint |
| Connect KB page to `/knowledge/` endpoints | Phase 3 endpoint |
| Connect Learning Feed to `/learning/` endpoints | Phase 3 endpoint |
| Connect Dashboard to `/dashboard/metrics` | Phase 3 endpoint |
| Add review approve/reject flow | Phase 3 review endpoint |
| Polish UI, loading states, error handling | All endpoints working |

**Milestone**: Full working demo end-to-end.

### Phase 5: Polish & Demo Prep

| Task | Depends On |
|------|------------|
| Run evaluation, get accuracy numbers | `/copilot/evaluate` |
| Prepare demo script (Section 11) | All features working |
| Add error boundaries and edge case handling | Phase 4 |
| Performance optimization (caching, etc.) | Phase 4 |

---

## 10. Environment & Configuration

### New Environment Variables

Add to `.env.example`:

```bash
# OpenAI (for embeddings + LLM agents)
OPENAI_API_KEY=your-openai-api-key
OPENAI_CHAT_MODEL=gpt-5

# SupportMind
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
KB_GAP_THRESHOLD=0.85
SEARCH_RESULT_LIMIT=5
```

### Config Updates

Add to `backend/api/core/config.py`:

```python
# SupportMind
OPENAI_CHAT_MODEL: str = "gpt-5"
EMBEDDING_MODEL: str = "text-embedding-3-small"
EMBEDDING_DIMENSIONS: int = 1536
KB_GAP_THRESHOLD: float = 0.85
SEARCH_RESULT_LIMIT: int = 5
```

---

## 11. Demo Script

**Duration**: 5 minutes

### Scene 1: "The Copilot" (1.5 min)
1. Open the Copilot page
2. Paste a question: *"Date advance fails because a backend voucher reference is invalid and needs a correction. PropertySuite Affordable."*
3. Show the classification: **SCRIPT** with 92% confidence
4. Show the top result: the exact matching script with placeholders highlighted
5. Show a secondary KB result with provenance trail

### Scene 2: "The Knowledge Gap" (1.5 min)
1. Navigate to Learning Feed — show existing approved/rejected events
2. Click "Detect Gap" for a specific ticket
3. System analyzes the ticket → detects no matching KB article
4. Shows the auto-generated draft article with provenance chain (Ticket → Conversation → Script)

### Scene 3: "The Learning Loop" (1 min)
1. Click "Approve" on the pending draft
2. Article status changes to Active
3. Go back to Copilot, ask a similar question
4. Show that the newly approved article now appears in results — **the system learned**

### Scene 4: "The Metrics" (1 min)
1. Show Dashboard with overall stats
2. Highlight: 3,207 KB articles, 161 auto-generated, 83% approval rate
3. Show retrieval accuracy: hit@1, hit@3, hit@5 on 1,000 ground-truth questions
4. Point out the category breakdown and root cause distribution

---

## Appendix: Evaluation Criteria Mapping

| Criterion | Where We Show It |
|-----------|-----------------|
| **Learning Capability** | Scene 2+3: gap detection → draft → approve → searchable |
| **Compliance & Safety** | Provenance trail, human-in-the-loop review gate, status workflow |
| **Accuracy & Consistency** | Scene 4: measurable hit@k on 1,000 ground-truth questions |
| **Automation & Scalability** | Async pipeline, pgvector handles 6k+ articles, batch processing |
| **Clarity of Demo** | 5-min script: input → classification → retrieval → learning → improvement |
| **Enterprise Readiness** | Role-based auth, audit trail, review workflow, Docker deployment |
