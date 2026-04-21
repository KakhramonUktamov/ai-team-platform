"""
Support Chatbot Agent — RAG-powered customer support.

Pipeline per question:
1. Search vector DB for relevant document chunks
2. Build context from top-k results
3. Generate answer grounded in retrieved docs
4. Score confidence based on retrieval relevance
5. Check if escalation to human is needed

Supports conversation history for multi-turn interactions.
"""

import json
from typing import Any, AsyncIterator

from config import settings
from core.base_agent import AgentOutput, BaseAgent
from core.ingestion import search_docs


class SupportChatbotAgent(BaseAgent):

    @property
    def agent_type(self) -> str:
        return "support-chatbot"

    @property
    def prompt_file(self) -> str:
        return "prompts/support_chatbot.yaml"

    def _build_context(self, chunks: list[dict]) -> str:
        """Format retrieved chunks into a context string for the prompt."""
        if not chunks:
            return "(No relevant documents found in knowledge base)"

        parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "unknown")
            score = chunk.get("relevance_score", 0)
            content = chunk.get("content", "")
            parts.append(f"[Source: {source} | Relevance: {score}]\n{content}")
        return "\n\n---\n\n".join(parts)

    def _format_history(self, history: list[dict]) -> str:
        """Format conversation history for the prompt."""
        if not history:
            return "(No previous messages)"

        lines = []
        for msg in history[-10:]:  # Keep last 10 messages max
            role = msg.get("role", "user")
            text = msg.get("content", "")
            prefix = "Customer" if role == "user" else "Agent"
            lines.append(f"{prefix}: {text}")
        return "\n".join(lines)

    def _calculate_confidence(self, chunks: list[dict]) -> float:
        """Calculate confidence based on retrieval relevance scores."""
        if not chunks:
            return 0.0

        scores = [c.get("relevance_score", 0) for c in chunks]
        top_score = max(scores)
        avg_score = sum(scores) / len(scores)

        # Weighted: top result matters most
        confidence = (top_score * 0.6) + (avg_score * 0.3) + (min(len(chunks) / 5, 1.0) * 0.1)
        return round(min(max(confidence, 0), 1), 3)

    async def _check_escalation(
        self, question: str, answer: str, history: list[dict], confidence: float
    ) -> dict:
        """Determine if the conversation should be escalated to a human."""
        # Quick rules first (no LLM call needed)
        lower_q = question.lower()
        if any(phrase in lower_q for phrase in ["speak to human", "talk to someone", "real person", "agent please"]):
            return {
                "should_escalate": True,
                "reason": "Customer requested human agent",
                "urgency": "high",
                "suggested_department": "support",
            }

        if confidence < 0.3:
            return {
                "should_escalate": True,
                "reason": "Very low confidence in AI answer",
                "urgency": "medium",
                "suggested_department": "support",
            }

        # For medium confidence, use LLM to decide
        if confidence < 0.6:
            try:
                system = self._render("system")
                check_prompt = self._render(
                    "escalation_check",
                    history=self._format_history(history),
                    question=question,
                    answer=answer,
                    confidence=confidence,
                )
                result = await self._call_llm(system, check_prompt)
                # Try to parse JSON from response
                result = result.strip()
                if result.startswith("```"):
                    result = result.split("\n", 1)[-1].rsplit("```", 1)[0]
                return json.loads(result)
            except (json.JSONDecodeError, Exception):
                return {
                    "should_escalate": True,
                    "reason": "Moderate confidence, escalation check inconclusive",
                    "urgency": "low",
                    "suggested_department": "support",
                }

        return {
            "should_escalate": False,
            "reason": "High confidence answer",
            "urgency": "low",
            "suggested_department": "",
        }

    async def run(self, input_data: dict[str, Any]) -> AgentOutput:
        question = input_data.get("question", "")
        workspace_id = input_data.get("workspace_id", "default")
        history = input_data.get("conversation_history", [])
        top_k = input_data.get("top_k", 5)

        if not question:
            raise ValueError("Question is required")

        self.logger.info("Processing support question", workspace=workspace_id)

        # Step 1: Retrieve relevant docs
        chunks = search_docs(query=question, workspace_id=workspace_id, top_k=top_k)
        context = self._build_context(chunks)
        confidence = self._calculate_confidence(chunks)
        self.logger.info("Retrieval complete", chunks=len(chunks), confidence=confidence)

        # Step 2: Generate answer
        system = self._render("system")
        answer_prompt = self._render(
            "answer",
            context=context,
            history=self._format_history(history),
            question=question,
        )
        answer = await self._call_llm(system, answer_prompt)
        self.logger.info("Answer generated")

        # Step 3: Check escalation
        escalation = await self._check_escalation(question, answer, history, confidence)
        self.logger.info("Escalation check", result=escalation)

        # Build source list
        sources = [
            {"source": c["source"], "relevance": c["relevance_score"]}
            for c in chunks[:3]
        ]

        return AgentOutput(
            content=answer,
            quality_score=round(confidence * 100, 1),
            tokens_used=0,
            model=settings.active_model,
            agent_type=self.agent_type,
            metadata={
                "workspace_id": workspace_id,
                "confidence": confidence,
                "sources": sources,
                "chunks_retrieved": len(chunks),
                "escalation": escalation,
                "question": question,
            },
        )

    async def run_stream(self, input_data: dict[str, Any]) -> AsyncIterator[str]:
        question = input_data.get("question", "")
        workspace_id = input_data.get("workspace_id", "default")
        history = input_data.get("conversation_history", [])
        top_k = input_data.get("top_k", 5)

        if not question:
            raise ValueError("Question is required")

        # Retrieve docs
        chunks = search_docs(query=question, workspace_id=workspace_id, top_k=top_k)
        context = self._build_context(chunks)

        # Stream answer
        system = self._render("system")
        answer_prompt = self._render(
            "answer",
            context=context,
            history=self._format_history(history),
            question=question,
        )
        async for chunk in self._stream_llm(system, answer_prompt):
            yield chunk
