"""
Email Marketer Agent — generates complete email marketing sequences.

Produces:
- Multi-email drip sequences (3-10 emails)
- Subject lines with A/B variants
- Preview text for each email
- Personalization tokens ({{first_name}}, etc.)
- CTA optimization
- Send timing recommendations

Uses a 3-step chain: sequence plan -> draft all emails -> polish.
"""

from typing import Any, AsyncIterator

from config import settings
from core.base_agent import AgentOutput, BaseAgent
from core.qa_pipeline import run_qa


VALID_GOALS = [
    "welcome_series",
    "trial_to_paid_conversion",
    "product_launch",
    "re_engagement",
    "upsell_cross_sell",
    "nurture_leads",
    "onboarding",
    "abandoned_cart",
    "event_promotion",
]


class EmailMarketerAgent(BaseAgent):

    @property
    def agent_type(self) -> str:
        return "email-marketer"

    @property
    def prompt_file(self) -> str:
        return "prompts/email_marketer.yaml"

    async def run(self, input_data: dict[str, Any]) -> AgentOutput:
        product = input_data.get("product", "")
        goal = input_data.get("goal", "nurture_leads")
        segment = input_data.get("segment", "all subscribers")
        email_count = input_data.get("email_count", 5)
        brand_voice = input_data.get("brand_voice", "professional, friendly")

        if not product:
            raise ValueError("Product/service description is required")

        email_count = max(2, min(email_count, 10))

        self.logger.info(
            "Starting email sequence generation",
            product=product, goal=goal, email_count=email_count,
        )

        system = self._render("system")

        # Step 1: Plan the sequence
        plan_prompt = self._render(
            "sequence_plan",
            product=product, goal=goal, segment=segment,
            email_count=email_count, brand_voice=brand_voice,
        )
        sequence_plan = await self._call_llm(system, plan_prompt)
        self.logger.info("Sequence plan complete")

        # Step 2: Draft all emails
        draft_prompt = self._render(
            "full_sequence",
            product=product, goal=goal, segment=segment,
            email_count=email_count, brand_voice=brand_voice,
            sequence_plan=sequence_plan,
        )
        draft = await self._call_llm(system, draft_prompt)
        self.logger.info("Full draft complete")

        # Step 3: Polish
        polish_prompt = self._render("polish", draft=draft)
        polished = await self._call_llm(system, polish_prompt)
        self.logger.info("Polish complete")

        # QA
        qa = run_qa(polished, min_words=200)

        # Parse email count from output
        actual_emails = polished.count("SUBJECT:")

        return AgentOutput(
            content=polished,
            quality_score=qa.overall_score,
            tokens_used=0,
            model=settings.active_model,
            agent_type=self.agent_type,
            metadata={
                "product": product,
                "goal": goal,
                "segment": segment,
                "email_count_target": email_count,
                "email_count_actual": actual_emails,
                "brand_voice": brand_voice,
                "word_count": qa.word_count,
                "readability": qa.readability_score,
                "qa_issues": qa.issues,
            },
        )

    async def run_stream(self, input_data: dict[str, Any]) -> AsyncIterator[str]:
        product = input_data.get("product", "")
        goal = input_data.get("goal", "nurture_leads")
        segment = input_data.get("segment", "all subscribers")
        email_count = input_data.get("email_count", 5)
        brand_voice = input_data.get("brand_voice", "professional, friendly")

        if not product:
            raise ValueError("Product/service description is required")

        email_count = max(2, min(email_count, 10))

        system = self._render("system")

        # Steps 1-2 run internally
        plan_prompt = self._render(
            "sequence_plan",
            product=product, goal=goal, segment=segment,
            email_count=email_count, brand_voice=brand_voice,
        )
        sequence_plan = await self._call_llm(system, plan_prompt)

        draft_prompt = self._render(
            "full_sequence",
            product=product, goal=goal, segment=segment,
            email_count=email_count, brand_voice=brand_voice,
            sequence_plan=sequence_plan,
        )
        draft = await self._call_llm(system, draft_prompt)

        # Step 3: Stream the polish step
        polish_prompt = self._render("polish", draft=draft)
        async for chunk in self._stream_llm(system, polish_prompt):
            yield chunk
