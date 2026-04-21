# AI Team Platform

AI-Powered Workforce Platform — 4 AI agents that replace traditional company roles.

## Agents

| Agent | Description | Status |
|-------|-------------|--------|
| **Content Writer** | Blog posts, social media, emails, product descriptions | Ready |
| **Email Marketer** | Drip sequences, subject lines, A/B variants, CTAs | Ready |
| **Support Chatbot** | RAG-powered customer support with escalation detection | Ready |
| **SEO Optimizer** | Keyword analysis, content audits, meta tags, optimization | Ready |

## Quick Start

```bash
# 1. Set up
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # edit: add OPENAI_API_KEY

# 2. Start infrastructure
docker-compose up -d

# 3. Test agents
python tests/test_content_writer.py
python tests/test_email_marketer.py
python tests/test_seo_optimizer.py
python tests/test_support_chatbot.py

# 4. Run the platform
uvicorn api.main:app --reload          # Terminal 1: API
streamlit run ui/app.py                # Terminal 2: UI
```

## API Endpoints

### Agent endpoints
- `GET /api/agents/types` — list all agents
- `POST /api/agents/{type}/run` — execute agent
- `POST /api/agents/{type}/stream` — execute + stream SSE

### Chat endpoints (support chatbot)
- `POST /api/chat/message` — ask a question
- `POST /api/chat/message/stream` — ask + stream
- `POST /api/chat/ingest/file` — upload PDF/DOCX/TXT to knowledge base
- `POST /api/chat/ingest/text` — paste text into knowledge base
- `GET /api/chat/documents` — list ingested documents
- `DELETE /api/chat/documents/{doc_id}` — remove document

## Switching LLM Providers

```bash
# OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key

# Anthropic (when ready)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
```

## Project Structure

```
agents/              4 AI agents
core/                Base agent, QA pipeline, document ingestion
api/routes/          FastAPI endpoints
prompts/             YAML prompt templates
integrations/        Third-party connectors (Phase 3)
analytics/           Usage tracking (Phase 4)
db/                  Database models (Phase 2)
ui/                  Streamlit dashboard
widget/              Embeddable chat widget (Phase 2)
tests/               Test scripts
```
