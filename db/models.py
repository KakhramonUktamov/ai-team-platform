"""
SQLAlchemy 2.0 models for the AI Team Platform.

Tables:
- users          — platform user accounts (mapped from Clerk)
- workspaces     — client workspace isolation (multi-tenant)
- executions     — every agent run logged here
- documents      — metadata for RAG-ingested files
- feedback       — user ratings on agent outputs
- chat_sessions  — support chatbot conversation history
- subscriptions  — Stripe subscription tracking (Phase 3)
5
All tables: id (UUID), created_at, updated_at.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    clerk_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="member")  # admin / member / viewer

    # Relationships
    workspaces: Mapped[list["Workspace"]] = relationship(back_populates="owner")


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    brand_guidelines: Mapped[Optional[str]] = mapped_column(Text)
    plan: Mapped[str] = mapped_column(String(50), default="starter")  # starter / growth / enterprise
    agents_enabled: Mapped[list[str]] = mapped_column(JSON, default=list)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)

    owner_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="workspaces")
    executions: Mapped[list["Execution"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")


class Execution(Base, TimestampMixin):
    __tablename__ = "executions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)

    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_text: Mapped[str] = mapped_column(Text, nullable=False)
    output_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    model: Mapped[str] = mapped_column(String(100), default="")

    # Relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="executions")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="execution", cascade="all, delete-orphan")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)

    doc_id: Mapped[str] = mapped_column(String(100), index=True)  # matches Chroma doc_id
    source: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(20))
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    total_chars: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="indexed")

    # Relationships
    workspace: Mapped["Workspace"] = relationship(back_populates="documents")


class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    execution_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("executions.id"), nullable=False, index=True)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # -1 (down), 0 (none), 1 (up)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    edit_diff: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    execution: Mapped["Execution"] = relationship(back_populates="feedback")


class ChatSession(Base, TimestampMixin):
    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)

    visitor_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    messages: Mapped[list[dict]] = mapped_column(JSON, default=list)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)
    resolved: Mapped[bool] = mapped_column(default=False)
    escalated: Mapped[bool] = mapped_column(default=False)
