"""
Chat endpoints — now with DB persistence for documents and sessions.
"""

import json
import os
import tempfile
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from agents.support_chatbot import SupportChatbotAgent
from api.auth import CurrentUser, get_current_user
from core.ingestion import (
    delete_document,
    ingest_file,
    ingest_text,
    list_documents,
)
from db.models import Document, Workspace
from db.session import get_db

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    question: str
    workspace_id: str = ""
    conversation_history: list[dict[str, Any]] = []
    top_k: int = 5


class IngestTextRequest(BaseModel):
    text: str
    source_name: str
    workspace_id: str = ""


async def _get_workspace_slug(db: AsyncSession, user: CurrentUser) -> str:
    """Get the slug of user's default workspace (used for Chroma namespacing)."""
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
        )
        db.add(workspace)
        await db.flush()
        await db.refresh(workspace)
    return workspace.slug, workspace.id


@router.post("/message")
async def chat_message(
    request: ChatMessage,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_slug, _ = await _get_workspace_slug(db, user)
    agent = SupportChatbotAgent()
    try:
        payload = request.model_dump()
        payload["workspace_id"] = ws_slug
        result = await agent.run(payload)
        return {
            "answer": result.content,
            "confidence": result.metadata["confidence"],
            "sources": result.metadata["sources"],
            "escalation": result.metadata["escalation"],
            "model": result.model,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/stream")
async def chat_message_stream(
    request: ChatMessage,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_slug, _ = await _get_workspace_slug(db, user)
    agent = SupportChatbotAgent()
    payload = request.model_dump()
    payload["workspace_id"] = ws_slug

    async def event_generator():
        try:
            full_text = ""
            async for chunk in agent.run_stream(payload):
                full_text += chunk
                yield {"event": "token", "data": json.dumps({"text": chunk, "done": False})}
            yield {"event": "complete", "data": json.dumps({"text": full_text, "done": True})}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


@router.post("/ingest/file")
async def ingest_document(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_slug, ws_id = await _get_workspace_slug(db, user)

    allowed = {".pdf", ".docx", ".txt", ".md", ".html", ".htm"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(allowed)}",
        )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        result = await ingest_file(
            file_path=tmp_path,
            workspace_id=ws_slug,
            source_name=file.filename,
        )

        # Persist document record
        doc = Document(
            workspace_id=ws_id,
            doc_id=result["doc_id"],
            source=result["source"],
            file_type=ext.lstrip("."),
            chunk_count=result["chunks_created"],
            total_chars=result["total_chars"],
            status="indexed",
        )
        db.add(doc)
        await db.flush()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/ingest/text")
async def ingest_raw_text(
    request: IngestTextRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_slug, ws_id = await _get_workspace_slug(db, user)

    try:
        result = await ingest_text(
            text=request.text,
            source_name=request.source_name,
            workspace_id=ws_slug,
        )

        doc = Document(
            workspace_id=ws_id,
            doc_id=result["doc_id"],
            source=result["source"],
            file_type="text",
            chunk_count=result["chunks_created"],
            total_chars=result["total_chars"],
            status="indexed",
        )
        db.add(doc)
        await db.flush()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def get_documents(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_slug, _ = await _get_workspace_slug(db, user)
    docs = list_documents(ws_slug)
    return {"documents": docs, "count": len(docs)}


@router.delete("/documents/{doc_id}")
async def remove_document(
    doc_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws_slug, ws_id = await _get_workspace_slug(db, user)

    deleted = delete_document(doc_id, ws_slug)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    # Also remove from DB
    result = await db.execute(
        select(Document).where(
            Document.doc_id == doc_id,
            Document.workspace_id == ws_id,
        )
    )
    db_doc = result.scalar_one_or_none()
    if db_doc:
        await db.delete(db_doc)

    return {"deleted_chunks": deleted, "doc_id": doc_id}
