from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import (
    AgentMessage,
    GeneratedFile,
    Workflow,
    WorkflowIteration,
    WorkflowStatus,
)


class WorkflowRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_workflow(self, prompt: str, workflow_id: str | None = None) -> Workflow:
        workflow = Workflow(
            prompt=prompt,
            status=WorkflowStatus.RUNNING,
            created_at=datetime.now(UTC),
        )
        if workflow_id:
            workflow.id = workflow_id
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        return self.db.scalars(
            select(Workflow).where(Workflow.id == workflow_id)
        ).first()

    def get_full_workflow(self, workflow_id: str) -> Workflow | None:
        return self.get_workflow(workflow_id)

    def mark_favorite(self, workflow_id: str) -> Workflow | None:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        workflow.favorite = True
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def remove_favorite(self, workflow_id: str) -> Workflow | None:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        workflow.favorite = False
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def get_favorites(self, limit: int = 10, offset: int = 0) -> tuple[list[Workflow], int]:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        query = select(Workflow).where(Workflow.favorite.is_(True))
        total_count = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        ordered_query = query.order_by(Workflow.created_at.desc()).offset(offset).limit(limit)
        items = list(self.db.scalars(ordered_query).all())
        return items, total_count

    def filter_by_date(self, query, date_range: str | None):
        if not date_range:
            return query

        norm_range = date_range.strip().lower()
        now = datetime.now(UTC)

        if norm_range == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif norm_range == "7d":
            from datetime import timedelta
            start_time = now - timedelta(days=7)
        elif norm_range == "30d":
            from datetime import timedelta
            start_time = now - timedelta(days=30)
        else:
            raise ValueError(f"Invalid date_range: {date_range}")

        return query.where(Workflow.created_at >= start_time)

    def list_workflows(
        self,
        limit: int = 10,
        offset: int = 0,
        search: str | None = None,
        status: str | None = None,
        date_range: str | None = None,
    ) -> tuple[list[Workflow], int]:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        query = select(Workflow)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.where(func.lower(Workflow.prompt).like(func.lower(search_pattern)))

        if status:
            norm_status = status.strip().upper()
            valid_statuses = [
                WorkflowStatus.RUNNING,
                WorkflowStatus.COMPLETE,
                WorkflowStatus.NEEDS_ATTENTION,
                WorkflowStatus.FAILED,
            ]
            if norm_status in valid_statuses:
                query = query.where(Workflow.status == norm_status)
            else:
                # If invalid status passed, match nothing or return empty
                return [], 0

        if date_range:
            query = self.filter_by_date(query, date_range)

        total_count = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0

        ordered_query = query.order_by(Workflow.created_at.desc()).offset(offset).limit(limit)
        items = list(self.db.scalars(ordered_query).all())

        return items, total_count

    def save_iteration(
        self,
        workflow_id: str,
        iteration_number: int,
        review_status: str | None = None,
        test_status: str | None = None,
        developer_output: str | None = None,
        reviewer_feedback: str | None = None,
        tester_feedback: str | None = None,
    ) -> WorkflowIteration:
        existing = self.db.scalars(
            select(WorkflowIteration).where(
                WorkflowIteration.workflow_id == workflow_id,
                WorkflowIteration.iteration_number == iteration_number,
            )
        ).first()

        if existing:
            if review_status is not None:
                existing.review_status = review_status
            if test_status is not None:
                existing.test_status = test_status
            if developer_output is not None:
                existing.developer_output = developer_output
            if reviewer_feedback is not None:
                existing.reviewer_feedback = reviewer_feedback
            if tester_feedback is not None:
                existing.tester_feedback = tester_feedback
            self.db.commit()
            self.db.refresh(existing)
            return existing

        iteration = WorkflowIteration(
            workflow_id=workflow_id,
            iteration_number=iteration_number,
            review_status=review_status,
            test_status=test_status,
            developer_output=developer_output,
            reviewer_feedback=reviewer_feedback,
            tester_feedback=tester_feedback,
            created_at=datetime.now(UTC),
        )
        self.db.add(iteration)
        self.db.commit()
        self.db.refresh(iteration)
        return iteration

    def save_message(
        self,
        workflow_id: str,
        agent_name: str,
        role: str,
        content: str,
        sequence_number: int,
        iteration_id: int | None = None,
        message_id: str | None = None,
        created_at: datetime | None = None,
    ) -> AgentMessage:
        msg = AgentMessage(
            workflow_id=workflow_id,
            iteration_id=iteration_id,
            agent_name=agent_name,
            role=role,
            content=content,
            sequence_number=sequence_number,
            created_at=created_at or datetime.now(UTC),
        )
        if message_id:
            msg.id = message_id
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def save_generated_file(
        self,
        workflow_id: str,
        filename: str,
        content: str,
        language: str = "python",
        is_final: bool = False,
        iteration_id: int | None = None,
    ) -> GeneratedFile:
        existing = self.db.scalars(
            select(GeneratedFile).where(
                GeneratedFile.workflow_id == workflow_id,
                GeneratedFile.iteration_id == iteration_id,
                GeneratedFile.filename == filename,
            )
        ).first()

        if existing:
            existing.content = content
            existing.language = language
            existing.is_final = is_final
            self.db.commit()
            self.db.refresh(existing)
            return existing

        gf = GeneratedFile(
            workflow_id=workflow_id,
            iteration_id=iteration_id,
            filename=filename,
            language=language,
            content=content,
            is_final=is_final,
            created_at=datetime.now(UTC),
        )
        self.db.add(gf)
        self.db.commit()
        self.db.refresh(gf)
        return gf

    def complete_workflow(
        self,
        workflow_id: str,
        final_summary: str | None = None,
        total_iterations: int = 1,
        status: str = WorkflowStatus.COMPLETE,
        quality_gate_data: str | None = None,
    ) -> Workflow | None:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None

        workflow.status = status
        workflow.final_summary = final_summary
        workflow.total_iterations = total_iterations
        if quality_gate_data is not None:
            workflow.quality_gate_data = quality_gate_data
        workflow.completed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def fail_workflow(
        self,
        workflow_id: str,
        failure_summary: str | None = None,
        total_iterations: int = 1,
    ) -> Workflow | None:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None

        workflow.status = WorkflowStatus.FAILED
        workflow.final_summary = failure_summary
        workflow.total_iterations = total_iterations
        workflow.completed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False

        self.db.delete(workflow)
        self.db.commit()
        return True

    def get_stats(self) -> dict:
        total_workflows = self.db.scalar(select(func.count(Workflow.id))) or 0
        completed_workflows = (
            self.db.scalar(
                select(func.count(Workflow.id)).where(Workflow.status == WorkflowStatus.COMPLETE)
            )
            or 0
        )
        failed_workflows = (
            self.db.scalar(
                select(func.count(Workflow.id)).where(Workflow.status == WorkflowStatus.FAILED)
            )
            or 0
        )
        needs_attention_workflows = (
            self.db.scalar(
                select(func.count(Workflow.id)).where(
                    Workflow.status == WorkflowStatus.NEEDS_ATTENTION
                )
            )
            or 0
        )
        running_workflows = (
            self.db.scalar(
                select(func.count(Workflow.id)).where(Workflow.status == WorkflowStatus.RUNNING)
            )
            or 0
        )
        favorite_count = (
            self.db.scalar(
                select(func.count(Workflow.id)).where(Workflow.favorite.is_(True))
            )
            or 0
        )

        avg_iter = (
            self.db.scalar(select(func.avg(Workflow.total_iterations)))
            or 0.0
        )

        return {
            "total_workflows": total_workflows,
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "needs_attention_workflows": needs_attention_workflows,
            "running_workflows": running_workflows,
            "favorite_count": favorite_count,
            "average_iterations": round(float(avg_iter), 2),
        }
