from typing import Any, AsyncGenerator
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_agentchat.base import TaskResult
from autogen_ext.models.ollama import OllamaChatCompletionClient

from agents.developer import create_python_developer_agent
from agents.manager import create_manager_agent
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL


def create_team(model_client: OllamaChatCompletionClient) -> RoundRobinGroupChat:
    manager_agent = create_manager_agent(model_client)
    developer_agent = create_python_developer_agent(model_client)
    termination = MaxMessageTermination(max_messages=3)
    return RoundRobinGroupChat(
        participants=[
            manager_agent,
            developer_agent,
        ],
        termination_condition=termination,
    )


def serialize_message(message: Any) -> dict:
    if isinstance(message, TaskResult):
        return {
            "id": "result",
            "source": "system",
            "type": "TaskResult",
            "content": f"Execution finished. Stop reason: {message.stop_reason or 'None'}",
            "created_at": "",
            "metadata": {"stop_reason": message.stop_reason} if message.stop_reason else {},
        }

    content = getattr(message, "content", "")
    if not isinstance(content, str):
        content = str(content)

    created_at_val = getattr(message, "created_at", None)
    created_at_str = created_at_val.isoformat() if created_at_val else ""

    return {
        "id": getattr(message, "id", ""),
        "source": getattr(message, "source", ""),
        "type": getattr(message, "type", message.__class__.__name__),
        "content": content,
        "created_at": created_at_str,
        "metadata": getattr(message, "metadata", {}) or {},
    }


async def run(task: str) -> None:
    model_client = OllamaChatCompletionClient(
        model=OLLAMA_MODEL,
        host=OLLAMA_BASE_URL,
    )

    try:
        team = create_team(model_client)
        await Console(team.run_stream(task=task))
    finally:
        await model_client.close()


async def run_workflow(task: str) -> dict:
    model_client = OllamaChatCompletionClient(
        model=OLLAMA_MODEL,
        host=OLLAMA_BASE_URL,
    )

    try:
        team = create_team(model_client)
        result = await team.run(task=task)
        serialized_messages = [serialize_message(msg) for msg in result.messages]
        return {
            "messages": serialized_messages,
            "stop_reason": result.stop_reason,
        }
    finally:
        await model_client.close()


async def run_workflow_stream(task: str) -> AsyncGenerator[dict, None]:
    model_client = OllamaChatCompletionClient(
        model=OLLAMA_MODEL,
        host=OLLAMA_BASE_URL,
    )

    try:
        team = create_team(model_client)
        async for event in team.run_stream(task=task):
            yield serialize_message(event)
    finally:
        await model_client.close()
