"""
Quick test - run the email marketer agent from command line.
Usage: python tests/test_email_marketer.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.email_marketer import EmailMarketerAgent


async def main():
    print("=" * 60)
    print("AI Team Platform - Email Marketer Test")
    print("=" * 60)

    agent = EmailMarketerAgent()
    print(f"\nProvider: {agent.llm.__class__.__name__}")
    print(f"Prompts loaded: {list(agent.prompts.keys())}\n")

    input_data = {
        "product": "TaskFlow - a project management SaaS for remote teams. Features: real-time collaboration, time tracking, automated standup reports. Pricing: $29/month per team.",
        "goal": "trial_to_paid_conversion",
        "segment": "users on day 3 of their 14-day free trial",
        "email_count": 5,
        "brand_voice": "friendly, helpful, slightly witty",
    }

    print(f"Product: {input_data['product'][:80]}...")
    print(f"Goal: {input_data['goal']}")
    print(f"Segment: {input_data['segment']}")
    print(f"Emails: {input_data['email_count']}")
    print(f"Voice: {input_data['brand_voice']}")
    print("\n" + "-" * 60)
    print("Generating (plan -> draft -> polish)...\n")

    result = await agent.run(input_data)

    print(result.content)
    print("\n" + "=" * 60)
    print(f"Quality Score: {result.quality_score}/100")
    print(f"Emails Generated: {result.metadata['email_count_actual']}")
    print(f"Total Words: {result.metadata['word_count']}")
    print(f"Model: {result.model}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
