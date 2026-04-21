"""
SEO Optimizer Agent — analyzes and optimizes content for search engines.

Modes:
1. keyword_analysis  — research keywords for a topic
2. content_audit     — score existing content and get fixes
3. meta_generator    — generate title tags, meta descriptions, schema
4. optimize_content  — rewrite content with SEO best practices

Each mode can run independently or chain together.
"""

import re
from typing import Any, AsyncIterator

from config import settings
from core.base_agent import AgentOutput, BaseAgent
from core.qa_pipeline import run_qa

VALID_MODES = ["keyword_analysis", "content_audit", "meta_generator", "optimize_content", "full_audit"]


class SEOOptimizerAgent(BaseAgent):

    @property
    def agent_type(self) -> str:
        return "seo-optimizer"

    @property
    def prompt_file(self) -> str:
        return "prompts/seo_optimizer.yaml"

    def _parse_seo_score(self, text: str) -> float:
        """Try to extract an SEO score from the audit output."""
        patterns = [
            r"OVERALL SEO SCORE:\s*(\d+)/100",
            r"SEO Score:\s*(\d+)/100",
            r"Overall:\s*(\d+)/100",
            r"(\d+)/100",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return 0.0

    async def _run_keyword_analysis(self, keywords: str, topic: str, audience: str) -> str:
        system = self._render("system")
        prompt = self._render(
            "keyword_analysis",
            keywords=keywords, topic=topic, audience=audience,
        )
        return await self._call_llm(system, prompt)

    async def _run_content_audit(self, keywords: str, content: str) -> str:
        system = self._render("system")
        prompt = self._render("content_audit", keywords=keywords, content=content)
        return await self._call_llm(system, prompt)

    async def _run_meta_generator(self, keywords: str, content: str) -> str:
        system = self._render("system")
        prompt = self._render("meta_generator", keywords=keywords, content=content)
        return await self._call_llm(system, prompt)

    async def _run_optimize_content(self, keywords: str, content: str) -> str:
        system = self._render("system")
        prompt = self._render("optimize_content", keywords=keywords, content=content)
        return await self._call_llm(system, prompt)

    async def run(self, input_data: dict[str, Any]) -> AgentOutput:
        mode = input_data.get("mode", "content_audit")
        keywords = input_data.get("keywords", "")
        content = input_data.get("content", "")
        topic = input_data.get("topic", "")
        audience = input_data.get("audience", "general audience")

        if not keywords and not topic:
            raise ValueError("Either keywords or topic is required")

        if mode in ("content_audit", "meta_generator", "optimize_content") and not content:
            raise ValueError(f"Content is required for mode: {mode}")

        self.logger.info("Starting SEO analysis", mode=mode)

        if mode == "keyword_analysis":
            result = await self._run_keyword_analysis(keywords or topic, topic or keywords, audience)
            seo_score = 0.0

        elif mode == "content_audit":
            result = await self._run_content_audit(keywords, content)
            seo_score = self._parse_seo_score(result)

        elif mode == "meta_generator":
            result = await self._run_meta_generator(keywords, content)
            seo_score = 0.0

        elif mode == "optimize_content":
            result = await self._run_optimize_content(keywords, content)
            seo_score = 0.0

        elif mode == "full_audit":
            # Run all steps in sequence
            self.logger.info("Running full audit (keyword + audit + meta + optimize)")

            kw_analysis = await self._run_keyword_analysis(
                keywords or topic, topic or keywords, audience
            )
            audit = await self._run_content_audit(keywords, content) if content else "No content provided for audit."
            metas = await self._run_meta_generator(keywords, content) if content else "No content provided for meta generation."
            optimized = await self._run_optimize_content(keywords, content) if content else "No content provided for optimization."

            seo_score = self._parse_seo_score(audit) if content else 0.0

            result = (
                "# Full SEO Audit Report\n\n"
                "---\n\n"
                "## 1. Keyword Research\n\n"
                f"{kw_analysis}\n\n"
                "---\n\n"
                "## 2. Content Audit\n\n"
                f"{audit}\n\n"
                "---\n\n"
                "## 3. Meta Tags\n\n"
                f"{metas}\n\n"
                "---\n\n"
                "## 4. Optimized Content\n\n"
                f"{optimized}"
            )
        else:
            raise ValueError(f"Invalid mode: {mode}. Valid: {VALID_MODES}")

        qa = run_qa(result, min_words=50)

        return AgentOutput(
            content=result,
            quality_score=seo_score if seo_score > 0 else qa.overall_score,
            tokens_used=0,
            model=settings.active_model,
            agent_type=self.agent_type,
            metadata={
                "mode": mode,
                "keywords": keywords,
                "topic": topic,
                "seo_score": seo_score,
                "word_count": qa.word_count,
            },
        )

    async def run_stream(self, input_data: dict[str, Any]) -> AsyncIterator[str]:
        mode = input_data.get("mode", "content_audit")
        keywords = input_data.get("keywords", "")
        content = input_data.get("content", "")
        topic = input_data.get("topic", "")
        audience = input_data.get("audience", "general audience")

        if not keywords and not topic:
            raise ValueError("Either keywords or topic is required")

        system = self._render("system")

        if mode == "keyword_analysis":
            prompt = self._render("keyword_analysis", keywords=keywords or topic, topic=topic or keywords, audience=audience)
        elif mode == "content_audit":
            prompt = self._render("content_audit", keywords=keywords, content=content)
        elif mode == "meta_generator":
            prompt = self._render("meta_generator", keywords=keywords, content=content)
        elif mode == "optimize_content":
            prompt = self._render("optimize_content", keywords=keywords, content=content)
        else:
            raise ValueError(f"Streaming not supported for mode: {mode}. Use 'run' for full_audit.")

        async for chunk in self._stream_llm(system, prompt):
            yield chunk
