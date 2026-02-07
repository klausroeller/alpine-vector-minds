o# SupportMind AI — Implementation Plan: Phase 4 & 5

**Date**: 2026-02-08
**Predecessor**: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) (Phases 1-3, all complete)
**Goal**: Push evaluation score from ~7.2/10 to ~9/10

---

## Table of Contents

1. [Score Gap Analysis](#1-score-gap-analysis)
2. [Phase 4A — Automatic Learning Loop](#2-phase-4a--automatic-learning-loop)
3. [Phase 4B — QA Scoring Agent](#3-phase-4b--qa-scoring-agent)
4. [Phase 4C — Copilot Feedback Loop](#4-phase-4c--copilot-feedback-loop)
5. [Phase 4D — Evaluation Metrics in Dashboard](#5-phase-4d--evaluation-metrics-in-dashboard)
6. [Phase 5A — Knowledge Quality Scoring](#6-phase-5a--knowledge-quality-scoring)
7. [Phase 5B — Root Cause Trend Detection](#7-phase-5b--root-cause-trend-detection)
8. [Updated Demo Script](#8-updated-demo-script)
9. [Updated Evaluation Criteria Mapping](#9-updated-evaluation-criteria-mapping)

---

## 1. Score Gap Analysis

### What's Blocking 9/10

| Criterion | Current | Target | Gap | Fix |
|-----------|---------|--------|-----|-----|
| Learning Capability | 7.5 | 9.5 | Loop is manual, not continuous | Phase 4A: auto-trigger on ticket resolution |
| Compliance & Safety | 3.0 | 7.5 | Not addressed at all | Phase 4B: QA scoring agent |
| Accuracy & Consistency | 8.0 | 9.0 | No feedback signal, no reranking | Phase 4C: copilot feedback |
| Automation & Scalability | 7.0 | 8.5 | No background workers | Phase 4A: background task |
| Clarity of Demo | 8.5 | 9.5 | Missing metrics visualization | Phase 4D: eval in dashboard |
| Enterprise Readiness | 7.0 | 8.5 | Missing audit, quality scoring | Phase 5A: knowledge quality |

### Priority Order

Phases 4A-4D are independent and can run in parallel. Phase 5 is stretch.

```
Phase 4A: Automatic Learning Loop ─────────┐
Phase 4B: QA Scoring Agent ────────────────┤── All independent, can parallelize
Phase 4C: Copilot Feedback Loop ───────────┤
Phase 4D: Eval Metrics in Dashboard ───────┘
                                            │
Phase 5A: Knowledge Quality Scoring ───────┤── Stretch goals
Phase 5B: Root Cause Trend Detection ──────┘
```

---

## 2. Phase 4A — Automatic Learning Loop

**Impact**: Learning Capability 7.5 → 9.5, Automation & Scalability 7.0 → 8.5
**Effort**: Medium
**Key insight**: The entire gap detection + KB generation pipeline already works. We just need to trigger it automatically instead of requiring a manual API call.

### 2A.1 Architecture

```
Ticket resolved (status → "resolved")
        │
        ▼
Background task enqueued
        │
        ▼
┌───────────────────────────┐
│  Auto-Learning Worker     │
│                           │
│  1. Fetch ticket + context│
│  2. Run GapDetectionAgent │
│  3. If gap: run KBGenAgent│
│  4. Create draft + lineage│
│  5. Create learning event │
│  6. (Pending → human rev) │
└───────────────────────────┘
```

### 2A.2 New: Background Task Runner

Since we want to avoid adding Redis/Celery for a hackathon, use FastAPI's built-in `BackgroundTasks` for fire-and-forget processing.

**File**: `backend/agents/auto_learning.py`

```python
"""Automatic learning loop — runs gap detection on resolved tickets."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from agents.gap_detection import GapDetectionAgent
from agents.kb_generation import KBGenerationAgent
from vector_db.embeddings import EmbeddingService
from vector_db.search import VectorSearchService

logger = logging.getLogger(__name__)


async def process_resolved_ticket(ticket_id: str) -> None:
    """
    Background task: detect knowledge gap from a resolved ticket
    and generate a draft KB article if needed.

    This is the same logic as the /learning/detect-gap endpoint,
    extracted into a standalone async function that can be called
    from BackgroundTasks.
    """
    # 1. Open a fresh DB session (background tasks outlive the request)
    async with get_async_session() as db:
        # 2. Check if already processed (idempotent)
        existing = await db.execute(
            select(LearningEvent)
            .where(LearningEvent.trigger_ticket_id == ticket_id)
        )
        if existing.scalar_one_or_none():
            logger.info(f"Ticket {ticket_id} already processed, skipping")
            return

        # 3. Run the same pipeline as /learning/detect-gap
        #    (extract shared logic from learning.py into this function)
        # ... fetch ticket, conversation, script
        # ... run GapDetectionAgent
        # ... if gap: run KBGenerationAgent
        # ... create draft article + lineage + learning event
        logger.info(f"Auto-learning complete for ticket {ticket_id}")
```

### 2A.3 New: Ticket Resolution Endpoint

Add a new endpoint that marks a ticket as resolved and triggers the learning loop.

**File**: `backend/api/v1/tickets.py` (new file)

```python
router = APIRouter()

class ResolveTicketRequest(BaseModel):
    resolution: str
    root_cause: str | None = None

@router.post("/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    request: ResolveTicketRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve a ticket and trigger automatic learning."""
    ticket = await _get_ticket(db, ticket_id)
    ticket.status = "resolved"
    ticket.resolution = request.resolution
    if request.root_cause:
        ticket.root_cause = request.root_cause
    await db.flush()

    # Fire-and-forget: auto-learning runs in background
    background_tasks.add_task(process_resolved_ticket, ticket_id)

    return {"id": ticket_id, "status": "resolved", "learning_triggered": True}
```

Register in `backend/api/v1/__init__.py`:
```python
from api.v1 import tickets
router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
```

### 2A.4 Refactor: Extract Shared Pipeline Logic

The detect-gap logic currently lives in `backend/api/v1/learning.py` (the `detect_gap` route handler). Extract it into a reusable function so both the manual endpoint and the background worker can call it.

**File**: `backend/agents/auto_learning.py`

Move the core pipeline logic (fetch ticket → gap detection → KB generation → save) into `run_learning_pipeline(db, ticket_id)`. Then:

- `learning.py` `detect_gap` endpoint calls `run_learning_pipeline(db, ticket_id)`
- `tickets.py` `resolve_ticket` endpoint calls `run_learning_pipeline(db, ticket_id)` via BackgroundTasks

### 2A.5 Frontend: "Resolve Ticket" UI

Add a minimal ticket detail page or a resolve action within the learning feed that lets the user resolve a ticket and see the learning loop trigger automatically.

**File**: `frontend/web/src/app/learning/page.tsx` — Add a "Trigger from Ticket" button that:
1. Shows a simple form: ticket ID, resolution text
2. Calls `POST /api/v1/tickets/{id}/resolve`
3. Shows a toast: "Ticket resolved. Learning pipeline running..."
4. After a short delay, refreshes the learning events list to show the new pending event

### 2A.6 API Client Extension

Add to `frontend/web/src/lib/api.ts`:
```typescript
resolveTicket: (ticketId: string, resolution: string, rootCause?: string) =>
  request<{ id: string; status: string; learning_triggered: boolean }>(
    `/api/v1/tickets/${ticketId}/resolve`,
    {
      method: 'POST',
      body: JSON.stringify({ resolution, root_cause: rootCause }),
    }
  ),
```

### 2A.7 Phase 4A Checklist

- [ ] Extract `run_learning_pipeline()` from `learning.py` into `agents/auto_learning.py`
- [ ] Update `learning.py` detect-gap endpoint to call extracted function
- [ ] Create `api/v1/tickets.py` with resolve endpoint + BackgroundTasks trigger
- [ ] Register tickets router
- [ ] Add `resolveTicket` to frontend API client
- [ ] Add "Resolve Ticket" UI to learning page (form + toast feedback)
- [ ] Test: resolve ticket → learning event appears automatically
- [ ] Update Makefile / README if needed

---

## 3. Phase 4B — QA Scoring Agent

**Impact**: Compliance & Safety 3.0 → 7.5
**Effort**: Medium
**Key insight**: The dataset ships a complete QA rubric (`QA_Evaluation_Prompt` tab) with weighted scoring and autozero red flags. We just need to wire it to an agent.

### 3B.1 Architecture

```
Conversation transcript + Ticket resolution
        │
        ▼
┌───────────────────────────────┐
│  QAScoringAgent               │
│                               │
│  Uses QA_Evaluation_Prompt    │
│  rubric from dataset as the   │
│  system prompt for LLM        │
│                               │
│  Scores:                      │
│  - Greeting & Empathy (10%)   │
│  - Issue Identification (15%) │
│  - Troubleshooting (20%)      │
│  - Resolution Accuracy (25%)  │
│  - Documentation (15%)        │
│  - Compliance & Safety (15%)  │
│                               │
│  Red Flags (autozero):        │
│  - Shared credentials         │
│  - Skipped verification       │
│  - Unauthorized data access   │
└───────────────────────────────┘
        │
        ▼
QA Score stored on conversation
```

### 3B.2 Data: Import QA Rubric

The `QA_Evaluation_Prompt` tab in the Excel file contains the full rubric text. Import it as a system prompt constant.

**File**: `backend/agents/qa_scoring.py`

```python
"""QA Scoring Agent — scores conversation quality using the RealPage rubric."""

from agents.base import BaseAgent, AgentMessage, AgentResponse

# The rubric from QA_Evaluation_Prompt tab (import once during data import
# or hardcode the rubric text as a constant)
QA_RUBRIC_PROMPT = """You are a QA evaluator for a customer support organization.
Score the following support interaction using these weighted criteria:

1. Greeting & Empathy (10%): Professional greeting, empathetic tone, active listening
2. Issue Identification (15%): Correct issue categorization, proper scoping questions
3. Troubleshooting Quality (20%): Logical steps, correct tool usage, efficiency
4. Resolution Accuracy (25%): Correct resolution, proper script execution, verified fix
5. Documentation Quality (15%): Complete case notes, correct categorization, knowledge linkage
6. Compliance & Safety (15%): Identity verification, no credential sharing, data privacy

AUTOZERO RED FLAGS (any one = 0 overall score):
- Agent shared or asked for login credentials
- Agent skipped identity verification for account changes
- Agent accessed or disclosed unauthorized customer data
- Agent provided financial or legal advice beyond scope

Return JSON:
{
  "overall_score": 0-100,
  "categories": {
    "greeting_empathy": {"score": 0-100, "feedback": "..."},
    "issue_identification": {"score": 0-100, "feedback": "..."},
    "troubleshooting": {"score": 0-100, "feedback": "..."},
    "resolution_accuracy": {"score": 0-100, "feedback": "..."},
    "documentation": {"score": 0-100, "feedback": "..."},
    "compliance_safety": {"score": 0-100, "feedback": "..."}
  },
  "red_flags": [],
  "summary": "..."
}"""


class QAScoringAgent(BaseAgent):
    """Scores a support interaction using the QA rubric."""

    async def run(self, messages: list[AgentMessage]) -> AgentResponse:
        # messages[0].content = JSON with transcript + ticket resolution
        response = await self._call_llm(
            system_prompt=QA_RUBRIC_PROMPT,
            user_message=messages[0].content,
            temperature=0.1,  # Low variance for consistent scoring
        )
        return AgentResponse(content=response, metadata={"agent": "qa_scoring"})
```

### 3B.3 Database: Add QA Score Fields

**File**: `backend/vector_db/models/conversation.py`

Add to the `Conversation` model:

```python
# QA scoring fields (populated by QAScoringAgent)
qa_score: Mapped[float | None]           # 0-100 overall score
qa_scores_json: Mapped[str | None]       # Full JSON breakdown (Text)
qa_red_flags: Mapped[str | None]         # Comma-separated red flag list
qa_scored_at: Mapped[datetime | None]    # When scoring was performed
```

### 3B.4 API: QA Scoring Endpoint

**File**: `backend/api/v1/qa.py` (new file)

```python
router = APIRouter()

@router.post("/score/{conversation_id}")
async def score_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QAScoreResponse:
    """Score a conversation transcript using the QA rubric."""
    conversation = await _get_conversation(db, conversation_id)
    ticket = await _get_ticket(db, conversation.ticket_id)

    agent = QAScoringAgent(...)
    result = await agent.run([AgentMessage(
        role="user",
        content=json.dumps({
            "transcript": conversation.transcript,
            "resolution": ticket.resolution,
            "category": ticket.category,
            "priority": ticket.priority,
        })
    )])

    # Parse and store scores
    scores = json.loads(result.content)
    conversation.qa_score = scores["overall_score"]
    conversation.qa_scores_json = result.content
    conversation.qa_red_flags = ",".join(scores.get("red_flags", []))
    conversation.qa_scored_at = datetime.now(UTC)
    await db.flush()

    return QAScoreResponse(**scores, conversation_id=conversation_id)


@router.get("/scores")
async def list_qa_scores(
    min_score: int | None = None,
    max_score: int | None = None,
    has_red_flags: bool | None = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    """List scored conversations with filters."""
    ...


@router.post("/score-batch")
async def score_batch(
    limit: int = 10,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Score unscored conversations in batch (background task)."""
    ...
```

Register in `backend/api/v1/__init__.py`:
```python
from api.v1 import qa
router.include_router(qa.router, prefix="/qa", tags=["qa"])
```

### 3B.5 Frontend: QA Scores Page

**File**: `frontend/web/src/app/qa/page.tsx` (new page)

| Element | Description |
|---------|-------------|
| Score distribution chart | Histogram of QA scores across all scored conversations |
| Red flag alerts | Highlighted cards for conversations with autozero red flags |
| Conversation score cards | List view with overall score, category breakdown, expandable feedback |
| "Score Batch" button | Admin action to trigger batch scoring of unscored conversations |

Add navigation entry:
| Route | Label | Icon (Lucide) |
|-------|-------|---------------|
| `/qa` | QA Scores | `ShieldCheck` |

### 3B.6 Dashboard Integration

Add QA metrics to the existing `/dashboard/metrics` response:

```json
{
  "qa": {
    "total_scored": 285,
    "average_score": 78.4,
    "red_flag_count": 12,
    "score_distribution": [
      { "range": "0-20", "count": 3 },
      { "range": "21-40", "count": 8 },
      { "range": "41-60", "count": 45 },
      { "range": "61-80", "count": 112 },
      { "range": "81-100", "count": 117 }
    ],
    "category_averages": {
      "greeting_empathy": 82.1,
      "issue_identification": 76.3,
      "troubleshooting": 74.8,
      "resolution_accuracy": 79.2,
      "documentation": 71.5,
      "compliance_safety": 85.7
    }
  }
}
```

### 3B.7 Phase 4B Checklist

- [ ] Import QA rubric text from `QA_Evaluation_Prompt` Excel tab (or hardcode from dataset)
- [ ] Implement `QAScoringAgent` in `backend/agents/qa_scoring.py`
- [ ] Add QA score columns to `Conversation` model
- [ ] Create `backend/api/v1/qa.py` with score + list + batch endpoints
- [ ] Register QA router
- [ ] Add QA metrics to dashboard endpoint
- [ ] Create frontend QA scores page
- [ ] Add QA chart to dashboard
- [ ] Add navigation entry for QA page
- [ ] Test: score a conversation → see breakdown → check red flags

---

## 4. Phase 4C — Copilot Feedback Loop

**Impact**: Learning Capability +0.5, Accuracy & Consistency +1.0
**Effort**: Low
**Key insight**: Even capturing the signal (without closing the loop fully) demonstrates awareness of the feedback cycle and provides data for future improvements.

### 4C.1 Database: Feedback Table

**File**: `backend/vector_db/models/copilot_feedback.py` (new file)

```python
class CopilotFeedback(Base):
    __tablename__ = "copilot_feedback"

    id: Mapped[str]                    # PK, UUID
    question_text: Mapped[str]         # The original question (Text)
    classification: Mapped[str]        # What the copilot classified (SCRIPT/KB/TICKET_RESOLUTION)
    result_id: Mapped[str]             # Which result the feedback is for
    result_rank: Mapped[int]           # Rank of the result (1-5)
    helpful: Mapped[bool]              # True = thumbs up, False = thumbs down
    user_id: Mapped[str]               # FK to users (who gave feedback)
    created_at: Mapped[datetime]
```

Register in `backend/vector_db/models/__init__.py`.

### 4C.2 API: Feedback Endpoint

**File**: `backend/api/v1/copilot.py` — Add to existing file

```python
class CopilotFeedbackRequest(BaseModel):
    question_text: str
    classification: str
    result_id: str
    result_rank: int
    helpful: bool

@router.post("/feedback")
async def submit_feedback(
    request: CopilotFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record copilot result feedback (thumbs up/down)."""
    feedback = CopilotFeedback(
        id=str(uuid.uuid4()),
        question_text=request.question_text,
        classification=request.classification,
        result_id=request.result_id,
        result_rank=request.result_rank,
        helpful=request.helpful,
        user_id=str(current_user.id),
        created_at=datetime.now(UTC),
    )
    db.add(feedback)
    await db.flush()
    return {"status": "recorded"}
```

### 4C.3 Dashboard Integration

Add feedback metrics to `/dashboard/metrics`:

```json
{
  "copilot_feedback": {
    "total_feedback": 156,
    "helpful_count": 112,
    "not_helpful_count": 44,
    "helpfulness_rate": 0.718,
    "by_classification": {
      "SCRIPT": { "helpful": 65, "not_helpful": 15 },
      "KB": { "helpful": 35, "not_helpful": 20 },
      "TICKET_RESOLUTION": { "helpful": 12, "not_helpful": 9 }
    }
  }
}
```

### 4C.4 Frontend: Feedback Buttons

**File**: `frontend/web/src/components/copilot/result-card.tsx` — Add to existing component

Add thumbs up / thumbs down buttons to each result card. On click:
1. Call `POST /api/v1/copilot/feedback`
2. Disable buttons (prevent double-submit)
3. Show brief "Thanks" confirmation

```typescript
// Add to api.ts
submitCopilotFeedback: (feedback: {
  question_text: string;
  classification: string;
  result_id: string;
  result_rank: number;
  helpful: boolean;
}) =>
  request<{ status: string }>('/api/v1/copilot/feedback', {
    method: 'POST',
    body: JSON.stringify(feedback),
  }),
```

### 4C.5 Phase 4C Checklist

- [ ] Create `copilot_feedback` model and register
- [ ] Add `POST /copilot/feedback` endpoint
- [ ] Add feedback metrics to dashboard endpoint
- [ ] Add thumbs up/down buttons to result cards in frontend
- [ ] Add feedback helpfulness chart to dashboard
- [ ] Test: search → thumbs down → see feedback in dashboard metrics

---

## 5. Phase 4D — Evaluation Metrics in Dashboard

**Impact**: Clarity of Demo 8.5 → 9.5
**Effort**: Low
**Key insight**: The `/copilot/evaluate` endpoint already computes everything. We just need to surface it in the UI and cache the results.

### 5D.1 Database: Evaluation Results Table

**File**: `backend/vector_db/models/evaluation_run.py` (new file)

```python
class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str]                    # PK, UUID
    total_questions: Mapped[int]
    classification_accuracy: Mapped[float]
    hit_at_1: Mapped[float]
    hit_at_3: Mapped[float]
    hit_at_5: Mapped[float]
    results_json: Mapped[str]          # Full breakdown as JSON (Text)
    started_at: Mapped[datetime]
    completed_at: Mapped[datetime]
    triggered_by: Mapped[str]          # user_id who triggered it
```

### 5D.2 API: Store Evaluation Results

Modify `backend/api/v1/copilot.py` `copilot_evaluate` to persist results:

```python
@router.get("/evaluate")
async def copilot_evaluate(...):
    # ... existing evaluation logic ...

    # NEW: persist the evaluation run
    run = EvaluationRun(
        id=str(uuid.uuid4()),
        total_questions=total,
        classification_accuracy=classification_acc,
        hit_at_1=hit_at_1,
        hit_at_3=hit_at_3,
        hit_at_5=hit_at_5,
        results_json=json.dumps(full_results),
        started_at=start_time,
        completed_at=datetime.now(UTC),
        triggered_by=str(current_user.id),
    )
    db.add(run)
    await db.flush()

    return response  # same response as before


@router.get("/evaluate/latest")
async def get_latest_evaluation(...):
    """Get the most recent evaluation run (cheap, cached in DB)."""
    result = await db.execute(
        select(EvaluationRun)
        .order_by(EvaluationRun.completed_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "No evaluation runs found. Run /copilot/evaluate first.")
    return { ... }
```

### 5D.3 Dashboard Integration

Add to `/dashboard/metrics` response:

```json
{
  "evaluation": {
    "latest_run": "2026-02-08T14:30:00Z",
    "classification_accuracy": 0.89,
    "hit_at_1": 0.72,
    "hit_at_3": 0.85,
    "hit_at_5": 0.91,
    "by_answer_type": {
      "SCRIPT": { "count": 700, "hit_at_1": 0.75, "hit_at_3": 0.88 },
      "KB": { "count": 209, "hit_at_1": 0.68, "hit_at_3": 0.82 },
      "TICKET_RESOLUTION": { "count": 91, "hit_at_1": 0.61, "hit_at_3": 0.76 }
    }
  }
}
```

### 5D.4 Frontend: Evaluation Dashboard Section

Add to `frontend/web/src/app/dashboard/page.tsx`:

**New components**:

1. **`EvaluationCard`** — Large card showing hit@1/3/5 as a bar chart or gauge
2. **`ClassificationAccuracyBadge`** — Prominent number: "89% classification accuracy"
3. **`PerTypeBreakdown`** — Small table: SCRIPT/KB/TICKET hit rates
4. **"Run Evaluation" button** — Admin-only, triggers `/copilot/evaluate` (with loading spinner, as it takes minutes)

Layout: Place evaluation section prominently at the top of the dashboard — it's the most impressive metric for judges.

### 5D.5 Phase 4D Checklist

- [ ] Create `evaluation_runs` model and register
- [ ] Modify `/copilot/evaluate` to persist results
- [ ] Add `GET /copilot/evaluate/latest` endpoint
- [ ] Add evaluation metrics to dashboard response
- [ ] Create `EvaluationCard` and `PerTypeBreakdown` frontend components
- [ ] Add evaluation section to dashboard page
- [ ] Add "Run Evaluation" admin button
- [ ] Test: run evaluation → see results on dashboard

---

## 6. Phase 5A — Knowledge Quality Scoring

**Impact**: Addresses a separate hero feature ("Knowledge Quality Dashboard"), Enterprise Readiness +0.5
**Effort**: Medium
**Prerequisite**: Phase 4C (feedback data) and Phase 4D (evaluation data)

### 6A.1 Quality Dimensions

Score each KB article on three dimensions:

| Dimension | How to Compute | Range |
|-----------|---------------|-------|
| **Freshness** | Days since last update, decaying score | 0-100 |
| **Usage** | Times retrieved by copilot (count from feedback + search logs) | 0-100 (normalized) |
| **Accuracy** | Helpfulness rate from copilot feedback for this article | 0-100 |

**Overall quality = weighted average**: Freshness (30%) + Usage (30%) + Accuracy (40%)

### 6A.2 Database: Quality Fields on KB Articles

Add to `KnowledgeArticle` model:

```python
# Quality scoring fields
quality_score: Mapped[float | None]       # 0-100 composite score
retrieval_count: Mapped[int]              # Times retrieved by copilot (default 0)
helpful_count: Mapped[int]                # Thumbs-up from copilot feedback (default 0)
not_helpful_count: Mapped[int]            # Thumbs-down from copilot feedback (default 0)
quality_scored_at: Mapped[datetime | None]
```

### 6A.3 Increment Counters on Copilot Usage

In the `/copilot/ask` handler, after returning results, increment `retrieval_count` for each returned article:

```python
# After search results are returned
for result in results:
    if result["source_type"] in ("KB", "knowledge_article"):
        await db.execute(
            update(KnowledgeArticle)
            .where(KnowledgeArticle.id == result["source_id"])
            .values(retrieval_count=KnowledgeArticle.retrieval_count + 1)
        )
```

Similarly, when copilot feedback is submitted, increment `helpful_count` or `not_helpful_count`.

### 6A.4 Quality Score Computation

**File**: `backend/scripts/compute_quality_scores.py` (or as a background task)

```python
async def compute_quality_scores(db: AsyncSession):
    """Recompute quality scores for all KB articles."""
    now = datetime.now(UTC)

    articles = await db.execute(select(KnowledgeArticle))
    for article in articles.scalars():
        # Freshness: 100 if updated today, decays by 1 per day, min 0
        days_old = (now - article.updated_at).days
        freshness = max(0, 100 - days_old)

        # Usage: normalize retrieval_count to 0-100
        # (use log scale to prevent outliers dominating)
        usage = min(100, (math.log1p(article.retrieval_count) / math.log1p(max_retrieval)) * 100)

        # Accuracy: helpfulness rate, default 50 if no feedback
        total_feedback = article.helpful_count + article.not_helpful_count
        if total_feedback > 0:
            accuracy = (article.helpful_count / total_feedback) * 100
        else:
            accuracy = 50  # neutral default

        article.quality_score = freshness * 0.3 + usage * 0.3 + accuracy * 0.4
        article.quality_scored_at = now
```

### 6A.5 Frontend: Quality Indicators

- Show quality score as a small badge on article cards in the KB list
- Add a "sort by quality" option to KB article filters
- Color-code: green (80+), yellow (50-79), red (<50)

### 6A.6 Phase 5A Checklist

- [ ] Add quality fields to `KnowledgeArticle` model
- [ ] Increment `retrieval_count` in copilot ask handler
- [ ] Increment `helpful_count` / `not_helpful_count` from copilot feedback
- [ ] Create `compute_quality_scores` script/task
- [ ] Add quality score badge to KB article cards
- [ ] Add "sort by quality" filter option
- [ ] Add quality distribution to dashboard

---

## 7. Phase 5B — Root Cause Trend Detection

**Impact**: Addresses "Root Cause Intelligence Mining" hero feature, Innovation +1.0
**Effort**: Medium

### 7B.1 Concept

Analyze tickets over time to identify:
1. **Emerging clusters**: Categories with increasing ticket volume
2. **Recurring failures**: Same root cause appearing across multiple accounts/properties
3. **Documentation gaps**: Categories where tickets are resolved but no KB articles exist

### 7B.2 API: Trend Detection Endpoint

**File**: `backend/api/v1/dashboard.py` — Add to existing

```python
@router.get("/trends")
async def get_trends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Identify root cause trends across tickets."""

    # 1. Category volume over time (by month)
    volume_by_month = await db.execute(text("""
        SELECT category,
               DATE_TRUNC('month', created_at) AS month,
               COUNT(*) AS count
        FROM tickets
        GROUP BY category, month
        ORDER BY month, count DESC
    """))

    # 2. Recurring root causes by property
    recurring = await db.execute(text("""
        SELECT root_cause, category, COUNT(*) AS count,
               COUNT(DISTINCT property_name) AS affected_properties
        FROM tickets
        GROUP BY root_cause, category
        HAVING COUNT(*) >= 3
        ORDER BY count DESC
        LIMIT 10
    """))

    # 3. Categories with tickets but no KB coverage
    gaps = await db.execute(text("""
        SELECT t.category, COUNT(*) AS ticket_count,
               COUNT(t.kb_article_id) AS with_kb,
               COUNT(*) - COUNT(t.kb_article_id) AS without_kb
        FROM tickets t
        GROUP BY t.category
        HAVING COUNT(*) - COUNT(t.kb_article_id) > 0
        ORDER BY without_kb DESC
    """))

    return {
        "volume_trends": [...],
        "recurring_issues": [...],
        "documentation_gaps": [...],
    }
```

### 7B.3 Frontend: Trends Section

Add to dashboard or as a separate `/trends` page:

1. **Line chart**: Ticket volume by category over time (shows emerging clusters)
2. **Alert cards**: "HAP/Voucher Processing has 15 tickets across 8 properties with no KB coverage"
3. **Root cause heatmap**: Categories vs. root causes, color-coded by count

### 7B.4 Phase 5B Checklist

- [ ] Implement `GET /dashboard/trends` endpoint
- [ ] Create trend visualization components (line chart, alert cards)
- [ ] Add trends section to dashboard or as standalone page
- [ ] Test with seed data: verify trends surface meaningful patterns

---

## 8. Updated Demo Script

**Duration**: 6-7 minutes (expanded from original 5 minutes)

### Scene 1: "The Copilot" (1.5 min)
*Same as original* — Ask a question, show classification + results + provenance.

### Scene 2: "The Self-Learning System" (2 min) **[EXPANDED]**
1. Show a resolved ticket in the system
2. **NEW**: Resolve the ticket via the UI → system automatically triggers learning
3. Watch the learning event appear in the feed (status: Pending)
4. Show the auto-generated draft article with provenance chain
5. Approve it → article becomes Active
6. Go back to Copilot → ask a related question → new article appears in results
7. **Key message**: "The system learned from a single ticket resolution — no human had to trigger anything."

### Scene 3: "Quality & Compliance" (1.5 min) **[NEW]**
1. Show the QA Scores page — overall distribution
2. Highlight a conversation with a red flag: "Agent shared credentials — autozero"
3. Show the category breakdown: troubleshooting quality is lowest → coaching opportunity
4. **Key message**: "Every interaction is scored for compliance. Red flags are caught automatically."

### Scene 4: "The Metrics That Matter" (1.5 min) **[EXPANDED]**
1. Show Dashboard with evaluation metrics prominently
2. **NEW**: Hit@1 = 72%, Hit@5 = 91% on 1,000 ground-truth questions
3. **NEW**: Copilot helpfulness rate from real feedback
4. Show KB categories, ticket priorities, learning approval rate
5. **NEW**: Show root cause trends — "HAP/Voucher Processing tickets increased 40% this month"
6. **Key message**: "We don't just answer questions — we measure how well we answer them and detect where the system needs to improve."

---

## 9. Updated Evaluation Criteria Mapping

| Criterion | Where We Show It | Expected Score |
|-----------|-----------------|----------------|
| **Learning Capability** | Scene 2: ticket resolved → auto gap detection → draft → approve → searchable. Continuous, not manual. | 9.5/10 |
| **Compliance & Safety** | Scene 3: QA scoring with rubric, autozero red flags, compliance category scoring | 7.5/10 |
| **Accuracy & Consistency** | Scene 4: measurable hit@k metrics, copilot feedback rate, quality scores on articles | 9.0/10 |
| **Automation & Scalability** | Background task learning, batch QA scoring, async pipeline, pgvector at scale | 8.5/10 |
| **Clarity of Demo** | Scene 1-4: input → classification → retrieval → auto-learning → QA scoring → metrics | 9.5/10 |
| **Enterprise Readiness** | Role-based auth, audit trail, QA compliance, quality scoring, trend detection, IaC | 8.5/10 |

**Projected composite: ~8.8/10**