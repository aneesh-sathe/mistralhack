"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-28 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _json_type():
    return sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("google_sub", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_sub"),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.Enum("PDF_UPLOADED", "PARSING", "PARSED", "FAILED", name="documentstatus", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("document_id", sa.CHAR(length=36), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("metadata", _json_type(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "modules",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("document_id", sa.CHAR(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("prerequisites", _json_type(), nullable=False),
        sa.Column("chunk_refs", _json_type(), nullable=False),
        sa.Column("status", sa.Enum("READY", "GENERATING", "DONE", "FAILED", name="modulestatus", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "module_assets",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("module_id", sa.CHAR(length=36), nullable=False),
        sa.Column("script_text", sa.Text(), nullable=True),
        sa.Column("script_json", _json_type(), nullable=False),
        sa.Column("manim_code", sa.Text(), nullable=True),
        sa.Column("audio_path", sa.String(length=1024), nullable=True),
        sa.Column("captions_srt_path", sa.String(length=1024), nullable=True),
        sa.Column("video_path", sa.String(length=1024), nullable=True),
        sa.Column("final_muxed_path", sa.String(length=1024), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "QUEUED",
                "RUNNING",
                "SCRIPT_DONE",
                "MANIM_DONE",
                "AUDIO_DONE",
                "CAPTIONS_DONE",
                "VIDEO_DONE",
                "MUXED_DONE",
                "FAILED",
                name="moduleassetstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_id", name="uq_module_assets_module_id"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.CHAR(length=36), nullable=False),
        sa.Column("user_id", sa.CHAR(length=36), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("payload", _json_type(), nullable=False),
        sa.Column("status", sa.Enum("queued", "running", "succeeded", "failed", name="jobstatus", native_enum=False), nullable=False),
        sa.Column("progress", _json_type(), nullable=False),
        sa.Column("result", _json_type(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("jobs")
    op.drop_table("module_assets")
    op.drop_table("modules")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("users")
