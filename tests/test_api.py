from unittest.mock import patch
import json
import pytest
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "service": "AutoGen API",
        "version": "0.2.0",
        "status": "running"
    }


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_chat_empty_task():
    # Test empty string task
    response = client.post("/api/chat", json={"task": ""})
    assert response.status_code == 422  # Pydantic validation error since min_length=1

    # Test whitespace-only task
    response = client.post("/api/chat", json={"task": "   "})
    assert response.status_code == 400
    assert "Task cannot be empty" in response.json()["detail"]

    # Test too long task (exceeding 5000 characters)
    response = client.post("/api/chat", json={"task": "a" * 5001})
    assert response.status_code == 422


def test_chat_stream_empty_task():
    # Test empty string task for streaming
    response = client.post("/api/chat/stream", json={"task": ""})
    assert response.status_code == 422  # Pydantic validation error since min_length=1

    # Test whitespace-only task for streaming
    response = client.post("/api/chat/stream", json={"task": "   "})
    assert response.status_code == 400
    assert "Task cannot be empty" in response.json()["detail"]


@patch("app.api.run_workflow")
def test_chat_non_streaming_success(mock_run_workflow):
    # Setup mock return value
    mock_messages = [
        {
            "id": "msg-1",
            "source": "manager_agent",
            "type": "TextMessage",
            "content": "Hello, how can I help you?",
            "created_at": "2026-07-26T19:00:00Z",
            "metadata": {},
        },
        {
            "id": "msg-2",
            "source": "python_developer",
            "type": "TextMessage",
            "content": "I am working on the Python code.",
            "created_at": "2026-07-26T19:00:05Z",
            "metadata": {},
        }
    ]
    mock_run_workflow.return_value = {
        "messages": mock_messages,
        "stop_reason": "Max messages reached",
    }

    # Execute request
    response = client.post("/api/chat", json={"task": "Write print script"})
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 2
    assert data["messages"][0]["source"] == "manager_agent"
    assert data["messages"][1]["content"] == "I am working on the Python code."
    assert data["stop_reason"] == "Max messages reached"
    
    # Verify mock was called correctly
    mock_run_workflow.assert_called_once_with("Write print script")


@patch("app.api.run_workflow")
def test_chat_non_streaming_error_masking(mock_run_workflow):
    # Setup mock to raise a raw connection or setup exception
    mock_run_workflow.side_effect = RuntimeError("Could not connect to Ollama service")

    # Execute request
    response = client.post("/api/chat", json={"task": "Write print script"})
    
    # Assertions
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


@patch("app.api.run_workflow_stream")
def test_chat_streaming_success(mock_run_workflow_stream):
    # Setup mock async generator
    async def mock_generator(task):
        yield {
            "id": "msg-1",
            "source": "manager_agent",
            "type": "TextMessage",
            "content": f"Streaming manager for task: {task}",
            "created_at": "2026-07-26T19:00:00Z",
            "metadata": {},
        }
        yield {
            "id": "msg-2",
            "source": "python_developer",
            "type": "TextMessage",
            "content": "Streaming developer",
            "created_at": "2026-07-26T19:00:01Z",
            "metadata": {},
        }

    mock_run_workflow_stream.side_effect = mock_generator

    # Execute request
    response = client.post("/api/chat/stream", json={"task": "Write test script"})
    
    # Assertions
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # Read streamed events
    events = []
    for line in response.iter_lines():
        if line.startswith("data: "):
            json_str = line[len("data: "):]
            events.append(json.loads(json_str))
            
    assert len(events) == 2
    assert events[0]["source"] == "manager_agent"
    assert "Write test script" in events[0]["content"]
    assert events[1]["source"] == "python_developer"
    assert events[1]["content"] == "Streaming developer"
    
    # Verify mock was called correctly
    mock_run_workflow_stream.assert_called_once_with("Write test script")


@patch("app.api.run_workflow_stream")
def test_chat_streaming_error_masking(mock_run_workflow_stream):
    # Setup mock async generator that raises an exception
    async def mock_generator(task):
        yield {
            "id": "msg-1",
            "source": "manager_agent",
            "type": "TextMessage",
            "content": "Running...",
            "created_at": "2026-07-26T19:00:00Z",
            "metadata": {},
        }
        raise RuntimeError("Ollama crashed mid-way")

    mock_run_workflow_stream.side_effect = mock_generator

    # Execute request
    response = client.post("/api/chat/stream", json={"task": "Write test script"})
    
    # Assertions
    assert response.status_code == 200
    
    events = []
    for line in response.iter_lines():
        if line.startswith("data: "):
            json_str = line[len("data: "):]
            events.append(json.loads(json_str))
            
    assert len(events) == 2
    assert events[0]["content"] == "Running..."
    assert events[1]["type"] == "Error"
    assert events[1]["content"] == "Internal server error"
