import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.database.repository import WorkflowRepository
from app.database.schemas import (
    WorkflowDetailSchema,
    WorkflowListSchema,
    WorkflowStatsSchema,
    WorkflowSummarySchema,
)
from app.runner import run_workflow, run_workflow_stream

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")
# Silence internal autogen_core trace logs
logging.getLogger("autogen_core.trace").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    init_db()
    yield


app = FastAPI(title="AutoGen API Gateway", version="0.2.0", lifespan=lifespan)

# CORS setup for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4201",
        "http://127.0.0.1:4201",
        "http://172.18.70.101:4201",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskRequest(BaseModel):
    task: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The task to pass to the agent team",
    )


class MessageResponse(BaseModel):
    id: str
    source: str
    type: str
    content: str
    created_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    messages: list[MessageResponse]
    stop_reason: str | None = None


@app.get("/")
async def root_endpoint():
    return {"service": "AutoGen API", "version": "0.2.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/chat", response_model=TaskResponse)
async def chat_non_streaming(request: TaskRequest):
    task = request.task.strip()
    if not task:
        raise HTTPException(
            status_code=400, detail="Task cannot be empty or only whitespace"
        )

    try:
        result = await run_workflow(task)
        return result
    except Exception:
        logger.exception("An error occurred during non-streaming chat execution")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/chat/stream")
async def chat_streaming(request: TaskRequest):
    task = request.task.strip()
    if not task:
        raise HTTPException(
            status_code=400, detail="Task cannot be empty or only whitespace"
        )

    async def event_generator():
        try:
            async for event in run_workflow_stream(task):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            logger.exception("An error occurred during streaming chat execution")
            error_event = {
                "id": "error",
                "source": "system",
                "type": "Error",
                "content": "Internal server error",
                "created_at": "",
                "metadata": {},
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- Workflow History Endpoints ---


@app.get("/api/workflows", response_model=WorkflowListSchema)
async def list_workflows(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    repo = WorkflowRepository(db)
    items, total = repo.list_workflows(
        limit=limit, offset=offset, search=search, status=status
    )
    summaries = [WorkflowSummarySchema(**wf.to_dict()) for wf in items]
    return WorkflowListSchema(
        items=summaries,
        total=total,
        limit=limit,
        offset=offset,
    )


@app.get("/api/workflows/stats", response_model=WorkflowStatsSchema)
async def get_workflow_stats(db: Session = Depends(get_db)):
    repo = WorkflowRepository(db)
    stats = repo.get_stats()
    return WorkflowStatsSchema(**stats)


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowDetailSchema)
async def get_workflow_detail(workflow_id: str, db: Session = Depends(get_db)):
    repo = WorkflowRepository(db)
    wf = repo.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    wf_dict = wf.to_dict()

    # Iterations sorted by iteration_number
    iterations = [it.to_dict() for it in sorted(wf.iterations, key=lambda x: x.iteration_number)]

    # Messages sorted by sequence_number
    messages = [msg.to_dict() for msg in sorted(wf.messages, key=lambda x: x.sequence_number)]

    # Generated files sorted with final files first, then created_at
    generated_files = [
        gf.to_dict()
        for gf in sorted(
            wf.generated_files,
            key=lambda x: (not x.is_final, x.created_at or ""),
        )
    ]

    return WorkflowDetailSchema(
        id=wf_dict["id"],
        prompt=wf_dict["prompt"],
        status=wf_dict["status"],
        final_summary=wf_dict["final_summary"],
        total_iterations=wf_dict["total_iterations"],
        generated_file_count=wf_dict["generated_file_count"],
        created_at=wf_dict["created_at"],
        completed_at=wf_dict["completed_at"],
        iterations=iterations,
        messages=messages,
        generated_files=generated_files,
    )


@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, db: Session = Depends(get_db)):
    repo = WorkflowRepository(db)
    deleted = repo.delete_workflow(workflow_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"status": "deleted", "workflow_id": workflow_id}
