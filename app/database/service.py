import logging
from typing import Any

from app.database.connection import SessionLocal, init_db
from app.database.models import WorkflowStatus
from app.database.repository import WorkflowRepository

logger = logging.getLogger("persistence_service")


class WorkflowPersistenceService:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        bind = None
        if hasattr(session_factory, "kw") and isinstance(session_factory.kw, dict):
            bind = session_factory.kw.get("bind")
        init_db(bind)

    def start_workflow(self, prompt: str, workflow_id: str | None = None) -> str:
        with self.session_factory() as db:
            repo = WorkflowRepository(db)
            wf = repo.create_workflow(prompt=prompt, workflow_id=workflow_id)
            return wf.id

    def record_agent_message(
        self,
        workflow_id: str,
        message: dict[str, Any],
        sequence_number: int,
        iteration: int = 1,
    ) -> None:
        with self.session_factory() as db:
            repo = WorkflowRepository(db)

            # Get iteration db record id if exists
            iter_record = repo.save_iteration(
                workflow_id=workflow_id,
                iteration_number=iteration,
            )

            source = message.get("source", "system")
            role = message.get("type", "TextMessage")
            content = message.get("content", "")
            msg_id = message.get("id")

            repo.save_message(
                workflow_id=workflow_id,
                agent_name=source,
                role=role,
                content=content,
                sequence_number=sequence_number,
                iteration_id=iter_record.id,
                message_id=msg_id if msg_id and msg_id not in ("result", "error") else None,
            )

    def record_iteration(
        self,
        workflow_id: str,
        iteration: int,
        review_status: str | None = None,
        test_status: str | None = None,
        developer_output: str | None = None,
        reviewer_feedback: str | None = None,
        tester_feedback: str | None = None,
    ) -> int:
        with self.session_factory() as db:
            repo = WorkflowRepository(db)
            iter_rec = repo.save_iteration(
                workflow_id=workflow_id,
                iteration_number=iteration,
                review_status=review_status,
                test_status=test_status,
                developer_output=developer_output,
                reviewer_feedback=reviewer_feedback,
                tester_feedback=tester_feedback,
            )
            return iter_rec.id

    def record_generated_files(
        self,
        workflow_id: str,
        files: list[dict[str, Any]],
        iteration: int = 1,
        is_final: bool = False,
    ) -> None:
        if not files:
            return

        with self.session_factory() as db:
            repo = WorkflowRepository(db)
            iter_rec = repo.save_iteration(
                workflow_id=workflow_id,
                iteration_number=iteration,
            )

            for file_info in files:
                filename = file_info.get("filename", "solution.py")
                content = file_info.get("content", "")
                language = file_info.get("language", "python")
                file_is_final = is_final or file_info.get("is_final", False)

                repo.save_generated_file(
                    workflow_id=workflow_id,
                    filename=filename,
                    content=content,
                    language=language,
                    is_final=file_is_final,
                    iteration_id=iter_rec.id,
                )

    def finish_workflow(
        self,
        workflow_id: str,
        status: str = WorkflowStatus.COMPLETE,
        final_summary: str | None = None,
        total_iterations: int = 1,
        quality_gate_data: str | None = None,
    ) -> None:
        with self.session_factory() as db:
            repo = WorkflowRepository(db)
            repo.complete_workflow(
                workflow_id=workflow_id,
                final_summary=final_summary,
                total_iterations=total_iterations,
                status=status,
                quality_gate_data=quality_gate_data,
            )

    def mark_failed(
        self,
        workflow_id: str,
        error_message: str,
        total_iterations: int = 1,
    ) -> None:
        with self.session_factory() as db:
            repo = WorkflowRepository(db)
            repo.fail_workflow(
                workflow_id=workflow_id,
                failure_summary=error_message,
                total_iterations=total_iterations,
            )
