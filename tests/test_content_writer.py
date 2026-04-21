"""
Quick test - run your content writer agent from the command line.
Usage: python tests/test_content_writer.py
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.content_writer import ContentWriterAgent


async def main():
    print("=" * 60)
    print("AI Team Platform - Content Writer Test")
    print("=" * 60)

    agent = ContentWriterAgent()
    print(f"\nProvider: {agent.llm.__class__.__name__}")
    print(f"Prompts loaded: {list(agent.prompts.keys())}\n")

    input_data = {
        "topic": "5 Python tricks that will make your code 10x cleaner",
        "format": "blog_post",
        "tone": "professional",
        "audience": "intermediate Python developers",
        "word_count": 600,
    }

    print(f"Topic: {input_data['topic']}")
    print(f"Format: {input_data['format']}")
    print(f"Tone: {input_data['tone']}")
    print(f"Audience: {input_data['audience']}")
    print(f"Target words: {input_data['word_count']}")
    print("\n" + "-" * 60)
    print("Generating (outline -> draft -> polish)...\n")

    result = await agent.run(input_data)

    print(result.content)
    print("\n" + "=" * 60)
    print(f"Quality Score: {result.quality_score}/100")
    print(f"Word Count: {result.metadata['word_count_actual']}")
    print(f"Readability: {result.metadata['readability']}")
    print(f"Reading Level: {result.metadata['reading_level']}")
    print(f"Model: {result.model}")
    if result.metadata.get("qa_issues"):
        print(f"QA Issues: {result.metadata['qa_issues']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
