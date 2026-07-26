import json
import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.runner import run_workflow, run_workflow_stream

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")
# Silence internal autogen_core trace logs (like dropping unrecognized 'host' key from create_args)
logging.getLogger("autogen_core.trace").setLevel(logging.WARNING)

app = FastAPI(title="AutoGen API Gateway", version="0.2.0")

# CORS setup for future Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
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
