from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base, GUID

JSONType = JSON().with_variant(JSONB, "postgresql")


class DocumentStatus(StrEnum):
    PDF_UPLOADED = "PDF_UPLOADED"
    PARSING = "PARSING"
    PARSED = "PARSED"
    FAILED = "FAILED"


class ModuleStatus(StrEnum):
    READY = "READY"
    GENERATING = "GENERATING"
    DONE = "DONE"
    FAILED = "FAILED"


class ModuleAssetStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SCRIPT_DONE = "SCRIPT_DONE"
    MANIM_DONE = "MANIM_DONE"
    AUDIO_DONE = "AUDIO_DONE"
    CAPTIONS_DONE = "CAPTIONS_DONE"
    VIDEO_DONE = "VIDEO_DONE"
    MUXED_DONE = "MUXED_DONE"
    FAILED = "FAILED"


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    documents: Mapped[list[Document]] = relationship(back_populates="user", cascade="all, delete-orphan")
    jobs: Mapped[list[Job]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False), default=DocumentStatus.PDF_UPLOADED, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="documents")
    chunks: Mapped[list[DocumentChunk]] = relationship(back_populates="document", cascade="all, delete-orphan")
    modules: Mapped[list[Module]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    meta: Mapped[dict] = mapped_column("metadata", JSONType, default=dict, nullable=False)

    document: Mapped[Document] = relationship(back_populates="chunks")


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    prerequisites: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    chunk_refs: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    status: Mapped[ModuleStatus] = mapped_column(
        Enum(ModuleStatus, native_enum=False), default=ModuleStatus.READY, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    document: Mapped[Document] = relationship(back_populates="modules")
    assets: Mapped[ModuleAsset | None] = relationship(back_populates="module", uselist=False, cascade="all, delete-orphan")


class ModuleAsset(Base):
    __tablename__ = "module_assets"
    __table_args__ = (UniqueConstraint("module_id", name="uq_module_assets_module_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    script_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    script_json: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    manim_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    captions_srt_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    video_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    final_muxed_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[ModuleAssetStatus] = mapped_column(
        Enum(ModuleAssetStatus, native_enum=False), default=ModuleAssetStatus.QUEUED, nullable=False
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    module: Mapped[Module] = relationship(back_populates="assets")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, native_enum=False), default=JobStatus.queued, nullable=False)
    progress: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    result: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="jobs")
