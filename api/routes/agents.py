"""
Agent execution endpoints — now with DB persistence.

Every run is logged to the executions table with full input/output,
quality scores, tokens, and latency.
"""

import json
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from agents import AGENT_REGISTRY, get_agent
from api.auth import CurrentUser, get_current_user
from db.models import Execution, Workspace
from db.session import get_db

router = APIRouter(tags=["agents"])


class AgentRequest(BaseModel):
    workspace_id: str = ""  # optional — defaults to user's first workspace
    # Content writer
    topic: str = ""
    format: str = "blog_post"
    tone: str = "professional"
    audience: str = "general audience"
    word_count: int = 800
    # Email marketer
    product: str = ""
    goal: str = "nurture_leads"
    segment: str = "all subscribers"
    email_count: int = 5
    brand_voice: str = "professional, friendly"
    # SEO
    keywords: str = ""
    content: str = ""
    mode: str = "content_audit"
    extra: dict[str, Any] = {}


async def _get_default_workspace(db: AsyncSession, user: CurrentUser) -> Workspace:
    """Find or create the user's default workspace."""
    result = await db.execute(
        select(Workspace).where(Workspace.owner_id == user.id).limit(1)
    )
    workspace = result.scalar_one_or_none()

    if workspace is None:
        workspace = Workspace(
            name="My Workspace",
            slug=f"ws-{user.id.hex[:8]}",
            owner_id=user.id,
            plan="starter",
            agents_enabled=list(AGENT_REGISTRY.keys()),
        )
        db.add(workspace)
        await db.flush()
        await db.refresh(workspace)

    return workspace


@router.get("/agents/types")
async def list_agent_types():
    return {
        "agents": [{"id": k, "name": k.replace("-", " ").title()} for k in AGENT_REGISTRY.keys()],
        "count": len(AGENT_REGISTRY),
    }


@router.post("/agents/{agent_type}/run")
async def run_agent(
    agent_type: str,
    request: AgentRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        agent = get_agent(agent_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    workspace = await _get_default_workspace(db, user)

    start = time.time()
    try:
        input_data = request.model_dump(exclude={"workspace_id", "extra"})
        result = await agent.run(input_data)
        latency_ms = int((time.time() - start) * 1000)

        # Persist execution
        execution = Execution(
            workspace_id=workspace.id,
            agent_type=agent_type,
            input_data=input_data,
            output_text=result.content,
            output_metadata=result.metadata,
            quality_score=result.quality_score,
            tokens_in=result.metadata.get("tokens_in", 0),
            tokens_out=result.metadata.get("tokens_out", 0),
            latency_ms=latency_ms,
            model=result.model,
        )
        db.add(execution)
        await db.flush()
        await db.refresh(execution)

        return {
            **result.model_dump(),
            "execution_id": str(execution.id),
            "workspace_id": str(workspace.id),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")


@router.post("/agents/{agent_type}/stream")
async def stream_agent(
    agent_type: str,
    request: AgentRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        agent = get_agent(agent_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    workspace = await _get_default_workspace(db, user)
    workspace_id = workspace.id
    input_data = request.model_dump(exclude={"workspace_id", "extra"})

    async def event_generator():
        from db.session import AsyncSessionLocal
        start = time.time()
        full_text = ""

        try:
            async for chunk in agent.run_stream(input_data):
                full_text += chunk
                yield {"event": "token", "data": json.dumps({"text": chunk, "done": False})}

            latency_ms = int((time.time() - start) * 1000)

            # Persist execution in fresh session (generator has its own lifecycle)
            async with AsyncSessionLocal() as session:
                execution = Execution(
                    workspace_id=workspace_id,
                    agent_type=agent_type,
                    input_data=input_data,
                    output_text=full_text,
                    output_metadata={"streaming": True},
                    quality_score=0.0,
                    latency_ms=latency_ms,
                    model="",
                )
                session.add(execution)
                await session.commit()
                await session.refresh(execution)
                exec_id = str(execution.id)

            yield {
                "event": "complete",
                "data": json.dumps({
                    "text": full_text,
                    "done": True,
                    "execution_id": exec_id,
                }),
            }
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


@router.get("/agents/history")
async def get_execution_history(
    agent_type: str = "",
    limit: int = 50,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent executions for the user's workspace."""
    workspace = await _get_default_workspace(db, user)

    query = select(Execution).where(Execution.workspace_id == workspace.id)
    if agent_type:
        query = query.where(Execution.agent_type == agent_type)
    query = query.order_by(desc(Execution.created_at)).limit(limit)

    result = await db.execute(query)
    executions = result.scalars().all()

    return {
        "executions": [
            {
                "id": str(e.id),
                "agent_type": e.agent_type,
                "created_at": e.created_at.isoformat(),
                "quality_score": e.quality_score,
                "latency_ms": e.latency_ms,
                "input_preview": str(e.input_data)[:200],
                "output_preview": e.output_text[:300],
                "model": e.model,
            }
            for e in executions
        ],
        "count": len(executions),
    }


@router.get("/agents/history/{execution_id}")
async def get_execution_detail(
    execution_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full execution details including complete output."""
    workspace = await _get_default_workspace(db, user)
    result = await db.execute(
        select(Execution).where(
            Execution.id == execution_id,
            Execution.workspace_id == workspace.id,
        )
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return {
        "id": str(execution.id),
        "agent_type": execution.agent_type,
        "created_at": execution.created_at.isoformat(),
        "input_data": execution.input_data,
        "output_text": execution.output_text,
        "output_metadata": execution.output_metadata,
        "quality_score": execution.quality_score,
        "latency_ms": execution.latency_ms,
        "tokens_in": execution.tokens_in,
        "tokens_out": execution.tokens_out,
        "model": execution.model,
    }
