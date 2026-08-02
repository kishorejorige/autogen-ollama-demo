import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class WorkflowStatus:
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    FAILED = "FAILED"


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=WorkflowStatus.RUNNING)
    final_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_iterations: Mapped[int] = mapped_column(Integer, default=0)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    iterations: Mapped[list["WorkflowIteration"]] = relationship(
        "WorkflowIteration",
        back_populates="workflow",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="WorkflowIteration.iteration_number",
    )

    messages: Mapped[list["AgentMessage"]] = relationship(
        "AgentMessage",
        back_populates="workflow",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AgentMessage.sequence_number",
    )

    generated_files: Mapped[list["GeneratedFile"]] = relationship(
        "GeneratedFile",
        back_populates="workflow",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "status": self.status,
            "final_summary": self.final_summary,
            "total_iterations": self.total_iterations,
            "favorite": bool(self.favorite) if self.favorite is not None else False,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "generated_file_count": len(self.generated_files),
        }


class WorkflowIteration(Base):
    __tablename__ = "workflow_iterations"
    __table_args__ = (
        UniqueConstraint("workflow_id", "iteration_number", name="uq_workflow_iteration"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    iteration_number: Mapped[int] = mapped_column(Integer, nullable=False)
    review_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    test_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    developer_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    tester_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="iterations")
    messages: Mapped[list["AgentMessage"]] = relationship("AgentMessage", back_populates="iteration")
    generated_files: Mapped[list["GeneratedFile"]] = relationship("GeneratedFile", back_populates="iteration")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "iteration_number": self.iteration_number,
            "review_status": self.review_status,
            "test_status": self.test_status,
            "developer_output": self.developer_output,
            "reviewer_feedback": self.reviewer_feedback,
            "tester_feedback": self.tester_feedback,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    iteration_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("workflow_iterations.id", ondelete="CASCADE"), nullable=True
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="messages")
    iteration: Mapped["WorkflowIteration | None"] = relationship("WorkflowIteration", back_populates="messages")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "iteration_id": self.iteration_id,
            "agent_name": self.agent_name,
            "role": self.role,
            "content": self.content,
            "sequence_number": self.sequence_number,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }


class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    iteration_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("workflow_iterations.id", ondelete="CASCADE"), nullable=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="python")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="generated_files")
    iteration: Mapped["WorkflowIteration | None"] = relationship("WorkflowIteration", back_populates="generated_files")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "iteration_id": self.iteration_id,
            "filename": self.filename,
            "language": self.language,
            "content": self.content,
            "is_final": self.is_final,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }
