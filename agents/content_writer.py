"""
Content Writer Agent - generates blog posts, social media, emails, product descriptions.
Uses a 3-step chain: outline -> draft -> polish.
"""

from typing import Any, AsyncIterator

from config import settings
from core.base_agent import AgentOutput, BaseAgent
from core.qa_pipeline import run_qa

VALID_FORMATS = ["blog_post", "social_media", "email_newsletter", "product_description"]
VALID_TONES = ["professional", "casual", "friendly", "authoritative", "witty", "empathetic"]


class ContentWriterAgent(BaseAgent):

    @property
    def agent_type(self) -> str:
        return "content-writer"

    @property
    def prompt_file(self) -> str:
        return "prompts/content_writer.yaml"

    async def run(self, input_data: dict[str, Any]) -> AgentOutput:
        topic = input_data.get("topic", "")
        format_type = input_data.get("format", "blog_post")
        tone = input_data.get("tone", "professional")
        audience = input_data.get("audience", "general audience")
        word_count = input_data.get("word_count", 800)

        if not topic:
            raise ValueError("Topic is required")

        self.logger.info("Starting content generation", topic=topic, format=format_type)

        # Step 1: Generate outline
        system = self._render("system")
        outline_prompt = self._render(
            "outline", topic=topic, format=format_type,
            tone=tone, audience=audience, word_count=word_count,
        )
        outline = await self._call_llm(system, outline_prompt)
        self.logger.info("Outline complete", length=len(outline))

        # Step 2: Write draft from outline
        draft_prompt = self._render(
            "draft", outline=outline, format=format_type,
            tone=tone, audience=audience, word_count=word_count,
        )
        draft = await self._call_llm(system, draft_prompt)
        self.logger.info("Draft complete", length=len(draft))

        # Step 3: Polish the draft
        polish_prompt = self._render("polish", draft=draft)
        polished = await self._call_llm(system, polish_prompt)
        self.logger.info("Polish complete", length=len(polished))

        # Run QA
        qa = run_qa(polished, min_words=100)
        self.logger.info("QA complete", score=qa.overall_score, issues=qa.issues)

        return AgentOutput(
            content=polished,
            quality_score=qa.overall_score,
            tokens_used=0,
            model=settings.active_model,
            agent_type=self.agent_type,
            metadata={
                "topic": topic,
                "format": format_type,
                "tone": tone,
                "audience": audience,
                "word_count_target": word_count,
                "word_count_actual": qa.word_count,
                "readability": qa.readability_score,
                "reading_level": qa.reading_level,
                "qa_issues": qa.issues,
            },
        )

    async def run_stream(self, input_data: dict[str, Any]) -> AsyncIterator[str]:
        """Stream the final polished output. Runs outline + draft internally first."""
        topic = input_data.get("topic", "")
        format_type = input_data.get("format", "blog_post")
        tone = input_data.get("tone", "professional")
        audience = input_data.get("audience", "general audience")
        word_count = input_data.get("word_count", 800)

        if not topic:
            raise ValueError("Topic is required")

        system = self._render("system")

        # Steps 1-2 run internally (not streamed)
        outline_prompt = self._render(
            "outline", topic=topic, format=format_type,
            tone=tone, audience=audience, word_count=word_count,
        )
        outline = await self._call_llm(system, outline_prompt)

        draft_prompt = self._render(
            "draft", outline=outline, format=format_type,
            tone=tone, audience=audience, word_count=word_count,
        )
        draft = await self._call_llm(system, draft_prompt)

        # Step 3: Stream the polish step
        polish_prompt = self._render("polish", draft=draft)
        async for chunk in self._stream_llm(system, polish_prompt):
            yield chunk
