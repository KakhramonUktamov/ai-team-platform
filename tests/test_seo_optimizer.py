"""
Test the SEO Optimizer agent in all modes.
Usage: python tests/test_seo_optimizer.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.seo_optimizer import SEOOptimizerAgent

SAMPLE_CONTENT = """
# How to Make Your Python Code Faster

Python is great but it can be slow. Here are some tips to speed it up.

## Use List Comprehensions
List comprehensions are faster than for loops. Instead of writing a loop,
write it in one line. This makes the code faster and cleaner.

## Avoid Global Variables
Global variables are slower to access. Use local variables when possible
inside your functions for better performance.

## Use Built-in Functions
Python built-in functions like map, filter, and sorted are implemented
in C and run much faster than custom Python loops.

## Profile Your Code
Use cProfile to find bottlenecks. Don't optimize blindly — measure first,
then fix the slowest parts.

## Conclusion
These tips will help make your Python code faster. Try them out and
see the difference in your projects.
"""


async def main():
    print("=" * 60)
    print("AI Team Platform - SEO Optimizer Test")
    print("=" * 60)

    agent = SEOOptimizerAgent()

    # Test 1: Keyword Analysis
    print("\n[1/4] Keyword Analysis...")
    result = await agent.run({
        "mode": "keyword_analysis",
        "keywords": "python performance optimization",
        "topic": "making Python code run faster",
        "audience": "intermediate Python developers",
    })
    print(f"  Words: {result.metadata['word_count']}")
    print(f"  Preview: {result.content[:200]}...")

    # Test 2: Content Audit
    print("\n[2/4] Content Audit...")
    result = await agent.run({
        "mode": "content_audit",
        "keywords": "python performance, python speed, optimize python code",
        "content": SAMPLE_CONTENT,
    })
    print(f"  SEO Score: {result.metadata['seo_score']}/100")
    print(f"  Preview: {result.content[:200]}...")

    # Test 3: Meta Generator
    print("\n[3/4] Meta Tag Generation...")
    result = await agent.run({
        "mode": "meta_generator",
        "keywords": "python performance optimization",
        "content": SAMPLE_CONTENT,
    })
    print(f"  Preview: {result.content[:300]}...")

    # Test 4: Content Optimization
    print("\n[4/4] Content Optimization...")
    result = await agent.run({
        "mode": "optimize_content",
        "keywords": "python performance, optimize python, python speed tips",
        "content": SAMPLE_CONTENT,
    })
    print(f"  Words: {result.metadata['word_count']}")
    print(f"  Preview: {result.content[:200]}...")

    print("\n" + "=" * 60)
    print("All SEO tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
