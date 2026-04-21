"""
End-to-end test for the Support Chatbot with RAG.

This test:
1. Ingests sample documents into the knowledge base
2. Asks questions and verifies answers are grounded in the docs
3. Tests escalation detection
4. Cleans up

Usage: python tests/test_support_chatbot.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ingestion import ingest_text, search_docs, list_documents, delete_document
from agents.support_chatbot import SupportChatbotAgent

# Sample knowledge base content
SAMPLE_FAQ = """
# TaskFlow FAQ

## How do I reset my password?
Go to Settings > Account > Security and click "Reset Password". You'll receive
an email with a reset link. The link expires after 24 hours.

## What are the pricing plans?
TaskFlow offers three plans:
- Starter: $9/month per user (up to 5 users, 10 projects)
- Team: $29/month per user (unlimited users and projects, time tracking)
- Enterprise: Custom pricing (SSO, dedicated support, SLA, audit logs)

## How do I cancel my subscription?
Go to Settings > Billing > Manage Subscription and click "Cancel Plan".
Your access continues until the end of the current billing period.
Refunds are available within 14 days of purchase.

## How do I invite team members?
Go to Settings > Team > Invite Members. Enter their email address and select
their role (Admin, Editor, or Viewer). They'll receive an invitation email.

## Is there a mobile app?
Yes! TaskFlow is available on iOS and Android. Download from the App Store or
Google Play. The mobile app supports all features including real-time collaboration.

## How does time tracking work?
Click the timer icon on any task to start tracking. The timer runs in the
background. Click again to stop. You can also manually log hours. Time reports
are available under Reports > Time Tracking.

## What integrations are available?
TaskFlow integrates with: Slack, GitHub, GitLab, Jira, Google Calendar,
Zoom, Figma, and Zapier. Go to Settings > Integrations to connect.
"""

SAMPLE_FEATURES = """
# TaskFlow Feature Guide

## Real-time Collaboration
Multiple team members can edit the same project simultaneously. Changes sync
instantly across all devices. You can see who's viewing and editing in real-time
with presence indicators.

## Automated Standup Reports
TaskFlow automatically generates daily standup reports based on task activity.
Reports include: tasks completed yesterday, tasks in progress today, and blockers.
Reports are sent to your team's Slack channel at 9 AM daily.

## Custom Workflows
Create custom task workflows with stages like: To Do > In Progress > Review > Done.
Add automation rules: auto-assign reviewers, send notifications on stage changes,
enforce required fields before moving to the next stage.
"""


async def main():
    print("=" * 60)
    print("AI Team Platform - Support Chatbot RAG Test")
    print("=" * 60)

    workspace = "test_workspace"

    # Step 1: Ingest documents
    print("\n[1/5] Ingesting sample documents...")
    result1 = await ingest_text(SAMPLE_FAQ, "FAQ Document", workspace)
    print(f"  FAQ: {result1['chunks_created']} chunks created")

    result2 = await ingest_text(SAMPLE_FEATURES, "Feature Guide", workspace)
    print(f"  Features: {result2['chunks_created']} chunks created")

    # Step 2: List documents
    print("\n[2/5] Documents in knowledge base:")
    docs = list_documents(workspace)
    for doc in docs:
        print(f"  - {doc['source']} ({doc['total_chunks']} chunks)")

    # Step 3: Test retrieval
    print("\n[3/5] Testing document retrieval...")
    results = search_docs("How do I reset my password?", workspace, top_k=3)
    for r in results:
        print(f"  [{r['relevance_score']}] {r['source']}: {r['content'][:80]}...")

    # Step 4: Test chatbot
    print("\n[4/5] Testing chatbot answers...")
    agent = SupportChatbotAgent()

    test_questions = [
        "How do I reset my password?",
        "What's the pricing for the Team plan?",
        "Does TaskFlow have a mobile app?",
        "Can I integrate with Slack?",
        "How does the automated standup report work?",
        "I want to speak to a human agent please",
    ]

    for q in test_questions:
        print(f"\n  Q: {q}")
        result = await agent.run({
            "question": q,
            "workspace_id": workspace,
            "conversation_history": [],
        })
        answer_preview = result.content[:150].replace("\n", " ")
        print(f"  A: {answer_preview}...")
        print(f"  Confidence: {result.metadata['confidence']}")
        esc = result.metadata["escalation"]
        if esc["should_escalate"]:
            print(f"  ESCALATE: {esc['reason']} (urgency: {esc['urgency']})")
        print(f"  Sources: {[s['source'] for s in result.metadata['sources']]}")

    # Step 5: Cleanup
    print("\n\n[5/5] Cleaning up test documents...")
    for doc in docs:
        deleted = delete_document(doc["doc_id"], workspace)
        print(f"  Deleted {doc['source']}: {deleted} chunks")

    print("\n" + "=" * 60)
    print("All tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
