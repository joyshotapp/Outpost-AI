"""RAG chat service for supplier AI avatar conversation"""

import asyncio
import json
import logging
from functools import partial
from typing import Optional

from app.services.claude import get_claude_service
from app.services.pinecone_knowledge import get_pinecone_knowledge_service

logger = logging.getLogger(__name__)


class RAGChatService:
    """Retrieve relevant chunks and generate answer with Claude"""

    ESCALATION_THRESHOLD = 70

    def __init__(self):
        self.pinecone = get_pinecone_knowledge_service()
        self.claude = get_claude_service()

    async def _claude_create(self, **kwargs) -> object:
        """Run the synchronous Anthropic SDK call in a thread pool so the
        async event loop is never blocked.  All keyword arguments are forwarded
        to ``client.messages.create``."""
        loop = asyncio.get_event_loop()
        fn = partial(self.claude.client.messages.create, **kwargs)
        return await loop.run_in_executor(None, fn)

    async def detect_language(self, text: str) -> str:
        system_prompt = (
            "Detect the language of the user text. "
            "Return strict JSON: {\"language\":\"xx\"} using ISO 639-1 code."
        )
        response = await self._claude_create(
            model=self.claude.model,
            max_tokens=128,
            system=system_prompt,
            messages=[{"role": "user", "content": text}],
        )
        self.claude.tracker.add_usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

        try:
            payload = json.loads(response.content[0].text)
            language = str(payload.get("language", "en")).lower().strip()
            if len(language) == 2:
                return language
        except Exception:
            logger.warning("Language detection fallback to en")
        return "en"

    async def translate_text(self, text: str, target_language: str, source_language: Optional[str] = None) -> str:
        if not text.strip():
            return text
        system_prompt = (
            "You are a professional translator for B2B manufacturing context. "
            "Translate text accurately and preserve technical terms and units."
        )
        source_hint = f"Source language: {source_language}\n" if source_language else ""
        user_prompt = (
            f"{source_hint}Target language: {target_language}\n"
            "Return only translated text without extra explanation.\n\n"
            f"Text:\n{text}"
        )
        response = await self._claude_create(
            model=self.claude.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        self.claude.tracker.add_usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return response.content[0].text.strip()

    def _compute_confidence(self, chunk_matches: list[dict]) -> int:
        if not chunk_matches:
            return 0
        avg_score = sum(float(match.get("score", 0)) for match in chunk_matches) / len(chunk_matches)
        confidence = int(min(100, max(0, round(avg_score * 100))))
        return confidence

    def _build_context(self, chunk_matches: list[dict]) -> str:
        if not chunk_matches:
            return ""

        blocks: list[str] = []
        for idx, match in enumerate(chunk_matches, start=1):
            chunk_text = match.get("chunk_text", "")
            source_title = match.get("source_title") or "Untitled"
            source_type = match.get("source_type") or "unknown"
            blocks.append(
                f"[Chunk {idx}] source={source_type}:{source_title}\n{chunk_text}"
            )
        return "\n\n".join(blocks)

    async def answer_question(
        self,
        supplier_id: int,
        question: str,
        language: str = "en",
        top_k: int = 5,
    ) -> dict:
        target_language = language.strip().lower() if language else "auto"
        detected_language = await self.detect_language(question)
        if target_language in {"", "auto"}:
            target_language = detected_language

        retrieval_query = question
        if detected_language != "en":
            retrieval_query = await self.translate_text(
                question,
                target_language="en",
                source_language=detected_language,
            )

        retrieval = self.pinecone.query_supplier_knowledge(
            supplier_id=supplier_id,
            query=retrieval_query,
            top_k=top_k,
        )
        matches = retrieval.get("matches", [])
        confidence_score = self._compute_confidence(matches)
        should_escalate = confidence_score < self.ESCALATION_THRESHOLD
        context = self._build_context(matches)

        if not context:
            return {
                "supplier_id": supplier_id,
                "question": question,
                "answer": "I don't have enough verified information in this supplier knowledge base. Please connect with a human sales representative.",
                "language": target_language,
                "confidence_score": confidence_score,
                "should_escalate": True,
                "matched_chunks": matches,
            }

        system_prompt = (
            "You are a B2B manufacturing sales assistant. "
            "Answer only based on provided context chunks. "
            "If information is insufficient, explicitly say you need human follow-up. "
            "Return JSON with keys: answer, grounded(boolean), missing_info(array)."
        )
        user_prompt = (
            f"Target language: {target_language}\n\n"
            f"Question: {question}\n\n"
            f"Knowledge Context:\n{context}"
        )

        response = await self._claude_create(
            model=self.claude.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        self.claude.tracker.add_usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

        raw_text = response.content[0].text
        answer = raw_text
        try:
            payload = json.loads(raw_text)
            answer = payload.get("answer", raw_text)
            if payload.get("grounded") is False:
                should_escalate = True
        except Exception:
            logger.warning("RAG answer is not valid JSON, falling back to raw output")

        # The system prompt already instructs Claude to answer in `target_language`,
        # so no additional translation step is needed here.  A second translate call
        # would double-translate and degrade quality.

        return {
            "supplier_id": supplier_id,
            "question": question,
            "answer": answer,
            "language": target_language,
            "confidence_score": confidence_score,
            "should_escalate": should_escalate,
            "matched_chunks": matches,
        }


_rag_chat_service: Optional[RAGChatService] = None


def get_rag_chat_service() -> RAGChatService:
    global _rag_chat_service
    if _rag_chat_service is None:
        _rag_chat_service = RAGChatService()
    return _rag_chat_service
