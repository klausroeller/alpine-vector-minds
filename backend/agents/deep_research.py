import asyncio
import json
import logging
import time
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AgentMessage, AgentResponse, BaseAgent, strip_markdown_fences
from agents.triage import TriageAgent, _secondary_pool
from api.core.constants import (
    DEEP_RESEARCH_MAX_CONTEXT_ITEMS,
    DEEP_RESEARCH_MAX_SUB_QUERIES,
    DEEP_RESEARCH_RESULTS_PER_QUERY,
    ENABLE_RERANKING,
    SEARCH_RESULT_LIMIT,
)
from vector_db.embeddings import EmbeddingService
from vector_db.embeddings import settings as embedding_settings
from vector_db.search import VectorSearchService

logger = logging.getLogger(__name__)

ROUTING_SYSTEM_PROMPT = """\
You are a query complexity router for a support knowledge system.
Given a user question, decide whether it requires SIMPLE lookup or RESEARCH (multi-step analysis).

SIMPLE: Direct factual lookups, single-topic questions, "how to X" questions, specific script requests.
RESEARCH: Questions that span multiple topics, require cross-referencing, need synthesized answers from \
multiple sources, ask for comparisons, root-cause analysis across systems, or comprehensive overviews.

Respond with ONLY one word: SIMPLE or RESEARCH\
"""

DECOMPOSITION_SYSTEM_PROMPT = """\
You are a query decomposition engine for a support knowledge system.
Given a complex question, break it into 2-4 focused sub-queries that together cover the full scope.

Each sub-query targets one of these pools:
- KB: Knowledge base articles (how-to guides, workflows, configuration)
- SCRIPT: SQL fix scripts (backend data fixes, remediation)
- TICKET_RESOLUTION: Past ticket resolutions (precedent, similar cases)

Respond ONLY with valid JSON (no markdown fences):
[{"query": "concise search query", "pool": "KB|SCRIPT|TICKET_RESOLUTION", "aspect": "what this sub-query investigates"}]\
"""

SYNTHESIS_SYSTEM_PROMPT = """\
You are a research synthesis engine for a support knowledge system.
Given a user question and search results from multiple sub-queries, produce a structured research report.

Rules:
- The summary should directly answer the question, synthesizing information across all sources
- Every claim in the summary must be traceable to a source_id in the evidence
- Evidence items should include the source_id exactly as provided in the search results
- Related resources are sources that are tangentially relevant but not directly cited in the summary
- If sources conflict, note the discrepancy in the summary
- Keep the summary concise but comprehensive (2-4 paragraphs)

Respond ONLY with valid JSON (no markdown fences):
{
  "summary": "synthesized answer to the question",
  "evidence": [
    {"source_id": "...", "source_type": "...", "title": "...", "relevance": "why this source matters", \
"content_preview": "key excerpt"}
  ],
  "related_resources": [
    {"source_id": "...", "source_type": "...", "title": "...", "why_relevant": "brief explanation"}
  ]
}\
"""

# Map pool labels to answer_type values used by search_all
_POOL_TO_ANSWER_TYPE: dict[str, str] = {
    "KB": "KB",
    "SCRIPT": "SCRIPT",
    "TICKET_RESOLUTION": "TICKET_RESOLUTION",
}


class DeepResearchAgent(BaseAgent):
    """Agentic deep research: decompose complex queries, parallel search, synthesize."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService | None = None,
        search_service: VectorSearchService | None = None,
    ) -> None:
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()
        self.search_service = search_service or VectorSearchService(db)
        self.llm_client = AsyncOpenAI(api_key=embedding_settings.OPENAI_API_KEY)
        self.fast_model = "gpt-4o-mini"
        self.synth_model = "gpt-4o"
        self.triage_agent = TriageAgent(db, self.embedding_service, self.search_service)

    async def run(self, messages: list[AgentMessage]) -> AgentResponse:
        start_time = time.perf_counter()
        question = messages[-1].content

        # Step 1: Route complexity
        route = await self._route_complexity(question)

        if route == "SIMPLE":
            # Delegate to TriageAgent
            triage_response = await self.triage_agent.run(messages)
            payload = json.loads(triage_response.content)
            result: dict[str, Any] = {
                "mode": "simple",
                "classification": payload.get("classification"),
                "results": payload.get("results", []),
            }
            total_ms = (time.perf_counter() - start_time) * 1000
            return AgentResponse(
                content=json.dumps(result),
                metadata={
                    **triage_response.metadata,
                    "total_time_ms": round(total_ms, 1),
                    "route": "simple",
                },
            )

        # Step 2: Classify + Decompose in parallel (both are LLM calls)
        classification, sub_queries = await asyncio.gather(
            self.triage_agent._classify(question),
            self._decompose(question),
        )

        # Step 3: Parallel search (sub-queries + baseline search using classification)
        merged_results = await self._parallel_search(sub_queries, classification)

        # Step 4: LLM rerank the merged candidates
        if ENABLE_RERANKING and merged_results:
            merged_results = await self.triage_agent._rerank(question, merged_results)

        # Step 5: Synthesize report from top results
        report = await self._synthesize(question, merged_results[:DEEP_RESEARCH_MAX_CONTEXT_ITEMS])

        total_ms = (time.perf_counter() - start_time) * 1000
        result = {
            "mode": "research",
            "classification": classification,
            "results": merged_results[:10],
            "report": report,
            "sub_queries": sub_queries,
        }

        return AgentResponse(
            content=json.dumps(result),
            metadata={
                "total_time_ms": round(total_ms, 1),
                "route": "research",
                "sub_query_count": len(sub_queries),
                "merged_result_count": len(merged_results),
            },
        )

    async def _route_complexity(self, question: str) -> str:
        try:
            completion = await self.llm_client.chat.completions.create(
                model=self.fast_model,
                messages=[
                    {"role": "system", "content": ROUTING_SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                max_completion_tokens=10,
            )
            raw = (completion.choices[0].message.content or "").strip().upper()
            if raw in ("SIMPLE", "RESEARCH"):
                return raw
            return "RESEARCH"
        except Exception:
            logger.exception("Complexity routing failed, defaulting to RESEARCH")
            return "RESEARCH"

    async def _decompose(self, question: str) -> list[dict[str, str]]:
        try:
            completion = await self.llm_client.chat.completions.create(
                model=self.fast_model,
                messages=[
                    {"role": "system", "content": DECOMPOSITION_SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                ],
                max_completion_tokens=500,
            )
            raw = strip_markdown_fences(completion.choices[0].message.content or "[]")
            parsed = json.loads(raw)

            if not isinstance(parsed, list) or not parsed:
                raise ValueError("Empty or invalid decomposition")

            # Validate and clamp
            sub_queries = []
            for item in parsed[:DEEP_RESEARCH_MAX_SUB_QUERIES]:
                pool = item.get("pool", "KB")
                if pool not in _POOL_TO_ANSWER_TYPE:
                    pool = "KB"
                sub_queries.append(
                    {
                        "query": item.get("query", question),
                        "pool": pool,
                        "aspect": item.get("aspect", ""),
                    }
                )
            return sub_queries

        except Exception:
            logger.exception("Decomposition failed, using raw question")
            return [{"query": question, "pool": "KB", "aspect": "general search"}]

    async def _parallel_search(
        self, sub_queries: list[dict[str, str]], classification: dict[str, Any]
    ) -> list[dict[str, Any]]:
        # Batch-embed all sub-query texts + the baseline search query in one call
        query_texts = [sq["query"] for sq in sub_queries]
        baseline_query = classification.get("search_query", "")
        query_texts.append(baseline_query)
        embeddings = await self.embedding_service.embed_batch(query_texts)

        # Split embeddings: sub-query embeddings + baseline embedding
        sub_embeddings = embeddings[:-1]
        baseline_embedding = embeddings[-1]

        # --- Sub-query searches ---
        async def _search_one(sq: dict[str, str], embedding: list[float]) -> list[dict[str, Any]]:
            answer_type = _POOL_TO_ANSWER_TYPE.get(sq["pool"], "KB")
            results, _ = await self.search_service.search_all(
                embedding,
                answer_type=answer_type,
                limit=DEEP_RESEARCH_RESULTS_PER_QUERY,
                raw_question=sq["query"],
            )
            for r in results:
                if "source_type" not in r:
                    r["source_type"] = answer_type
            return results

        # --- Baseline search (same as ask mode: primary + secondary pool) ---
        async def _baseline_search() -> list[dict[str, Any]]:
            primary_type = classification.get("answer_type", "KB")
            secondary_type = _secondary_pool(primary_type)
            primary_results, _ = await self.search_service.search_all(
                baseline_embedding,
                answer_type=primary_type,
                limit=SEARCH_RESULT_LIMIT,
                raw_question=baseline_query,
            )
            secondary_results, _ = await self.search_service.search_all(
                baseline_embedding,
                answer_type=secondary_type,
                limit=5,
                raw_question=baseline_query,
            )
            for r in primary_results:
                if "source_type" not in r:
                    r["source_type"] = primary_type
            for r in secondary_results:
                if "source_type" not in r:
                    r["source_type"] = secondary_type
            return primary_results + secondary_results

        # Launch all searches in parallel
        tasks = [_search_one(sq, emb) for sq, emb in zip(sub_queries, sub_embeddings, strict=True)]
        tasks.append(_baseline_search())
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge and deduplicate by id (keep highest score)
        seen: dict[str, dict[str, Any]] = {}
        for batch in all_results:
            if isinstance(batch, BaseException):
                logger.warning("Sub-query search failed: %s", batch)
                continue
            for item in batch:
                doc_id = item.get("id", "")
                if doc_id not in seen or item.get("similarity_score", 0) > seen[doc_id].get(
                    "similarity_score", 0
                ):
                    seen[doc_id] = item

        # Sort by score descending, take top N
        merged = sorted(seen.values(), key=lambda x: x.get("similarity_score", 0), reverse=True)
        return merged[:DEEP_RESEARCH_MAX_CONTEXT_ITEMS]

    async def _synthesize(self, question: str, results: list[dict[str, Any]]) -> dict[str, Any]:
        # Build context for the LLM
        context_lines = []
        valid_source_ids = set()
        for r in results:
            source_id = r.get("id", "")
            valid_source_ids.add(source_id)
            title = r.get("title", "")[:150]
            preview = r.get("content_preview", "")[:300]
            source_type = r.get("source_type", "")
            score = r.get("similarity_score", 0)
            context_lines.append(
                f"[{source_id}] (type: {source_type}, score: {score:.3f}) {title}\n{preview}"
            )

        context_block = "\n\n".join(context_lines)
        user_prompt = f"Question: {question}\n\nSearch results:\n{context_block}"

        try:
            completion = await self.llm_client.chat.completions.create(
                model=self.synth_model,
                messages=[
                    {"role": "system", "content": SYNTHESIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=2000,
            )
            raw = strip_markdown_fences(completion.choices[0].message.content or "{}")
            report = json.loads(raw)

            # Validate source_ids in evidence actually exist
            if "evidence" in report:
                report["evidence"] = [
                    e for e in report["evidence"] if e.get("source_id") in valid_source_ids
                ]
            if "related_resources" in report:
                report["related_resources"] = [
                    r for r in report["related_resources"] if r.get("source_id") in valid_source_ids
                ]

            return report

        except Exception:
            logger.exception("Synthesis failed, returning raw results as evidence")
            return {
                "summary": "Synthesis failed. Here are the raw search results ranked by relevance.",
                "evidence": [
                    {
                        "source_id": r.get("id", ""),
                        "source_type": r.get("source_type", ""),
                        "title": r.get("title", ""),
                        "relevance": f"Similarity score: {r.get('similarity_score', 0):.3f}",
                        "content_preview": r.get("content_preview", "")[:200],
                    }
                    for r in results[:10]
                ],
                "related_resources": [],
            }
