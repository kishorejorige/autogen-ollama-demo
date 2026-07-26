from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_core.models import (
    ChatCompletionClient,
    CreateResult,
    ModelCapabilities,
    RequestUsage,
)

from app.runner import (
    create_team,
    run,
    run_workflow,
    run_workflow_stream,
    serialize_message,
)


class MockModelClient(ChatCompletionClient):
    def __init__(self, model="", host="", *args, **kwargs):
        self.model = model
        self.host = host

    async def create(
        self,
        messages,
        tools=None,
        json_output=False,
        extra_create_args=None,
        cancellation_token=None,
    ):
        return CreateResult(
            content="Mock agent output. Review status: APPROVED",
            usage=RequestUsage(prompt_tokens=10, completion_tokens=20),
            finish_reason="stop",
            cached=False,
        )

    async def create_stream(
        self,
        messages,
        tools=None,
        json_output=False,
        extra_create_args=None,
        cancellation_token=None,
    ):
        pass

    @property
    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            vision=False, function_calling=False, json_output=False
        )

    @property
    def model_info(self):
        return {
            "vision": False,
            "function_calling": False,
            "json_output": False,
            "family": "unknown",
        }

    @property
    def actual_usage(self):
        return None

    @property
    def total_usage(self):
        return None

    @property
    def remaining_tokens(self):
        return None

    async def count_tokens(self, messages, tools=None):
        return 0

    async def close(self):
        pass


@patch("app.runner.RoundRobinGroupChat")
def test_agent_factories_and_names(mock_group_chat_class):
    client = MockModelClient()
    create_team(client)

    mock_group_chat_class.assert_called_once()
    args, kwargs = mock_group_chat_class.call_args
    participants = kwargs.get("participants") or args[0]

    assert len(participants) == 4

    names = [agent.name for agent in participants]
    assert names == [
        "manager_agent",
        "python_developer",
        "code_reviewer",
        "documentation_agent",
    ]

    for agent in participants:
        assert isinstance(agent, AssistantAgent)

    assert kwargs.get("max_turns") == 4


@patch("app.runner.create_documentation_agent")
@patch("app.runner.create_code_reviewer_agent")
@patch("app.runner.create_python_developer_agent")
@patch("app.runner.create_manager_agent")
def test_agent_factories_called_in_order(
    mock_manager, mock_developer, mock_reviewer, mock_documenter
):
    call_order = []

    # We use lambda or helper functions to record execution order without capturing
    # internal mock attribute lookups.
    mock_manager.side_effect = lambda *args, **kwargs: (
        call_order.append("manager"),
        MagicMock(),
    )[1]
    mock_developer.side_effect = lambda *args, **kwargs: (
        call_order.append("developer"),
        MagicMock(),
    )[1]
    mock_reviewer.side_effect = lambda *args, **kwargs: (
        call_order.append("reviewer"),
        MagicMock(),
    )[1]
    mock_documenter.side_effect = lambda *args, **kwargs: (
        call_order.append("documenter"),
        MagicMock(),
    )[1]

    client = MockModelClient()
    create_team(client)

    assert call_order == ["manager", "developer", "reviewer", "documenter"]


@patch("app.runner.create_team")
@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_fresh_team_per_request(mock_client_class, mock_create_team):
    mock_client_class.return_value = MockModelClient()
    mock_create_team.return_value = AsyncMock()

    await run_workflow("task 1")
    await run_workflow("task 2")

    assert mock_create_team.call_count == 2


def test_task_result_serialization():
    res = TaskResult(
        messages=[],
        stop_reason="Max turns reached",
    )
    serialized = serialize_message(res)
    assert serialized["id"] == "result"
    assert serialized["source"] == "system"
    assert serialized["type"] == "TaskResult"
    assert "Stop reason: Max turns reached" in serialized["content"]
    assert serialized["metadata"] == {"stop_reason": "Max turns reached"}


def test_task_result_serialization_no_stop_reason():
    res = TaskResult(
        messages=[],
        stop_reason=None,
    )
    serialized = serialize_message(res)
    assert serialized["id"] == "result"
    assert serialized["source"] == "system"
    assert serialized["type"] == "TaskResult"
    assert "Stop reason: None" in serialized["content"]
    assert serialized["metadata"] == {}


@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_streaming_agent_sources(mock_client_class):
    mock_client_class.return_value = MockModelClient()

    events = []
    async for event in run_workflow_stream("Do something"):
        events.append(event)

    # Expected: 1 user text message, 4 agent text messages, and 1 TaskResult
    assert len(events) == 6
    assert events[0]["source"] == "user"
    assert events[1]["source"] == "manager_agent"
    assert events[2]["source"] == "python_developer"
    assert events[3]["source"] == "code_reviewer"
    assert events[4]["source"] == "documentation_agent"
    assert events[5]["source"] == "system"
    assert events[5]["type"] == "TaskResult"


@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_run_workflow_cleanup_success(mock_client_class):
    mock_client = MockModelClient()
    mock_client.close = AsyncMock()
    mock_client_class.return_value = mock_client

    await run_workflow("test task")
    mock_client.close.assert_awaited_once()


@patch("app.runner.OllamaChatCompletionClient")
@patch("app.runner.create_team")
@pytest.mark.anyio
async def test_run_workflow_cleanup_failure(mock_create_team, mock_client_class):
    mock_client = MockModelClient()
    mock_client.close = AsyncMock()
    mock_client_class.return_value = mock_client

    mock_team = MagicMock()
    mock_team.run = AsyncMock(side_effect=RuntimeError("Test error"))
    mock_create_team.return_value = mock_team

    with pytest.raises(RuntimeError, match="Test error"):
        await run_workflow("test task")

    mock_client.close.assert_awaited_once()


@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_run_workflow_stream_cleanup_success(mock_client_class):
    mock_client = MockModelClient()
    mock_client.close = AsyncMock()
    mock_client_class.return_value = mock_client

    async for _ in run_workflow_stream("test task"):
        pass

    mock_client.close.assert_awaited_once()


@patch("app.runner.OllamaChatCompletionClient")
@patch("app.runner.create_team")
@pytest.mark.anyio
async def test_run_workflow_stream_cleanup_failure(mock_create_team, mock_client_class):
    mock_client = MockModelClient()
    mock_client.close = AsyncMock()
    mock_client_class.return_value = mock_client

    mock_team = MagicMock()
    mock_team.run_stream = MagicMock(side_effect=RuntimeError("Stream crash"))
    mock_create_team.return_value = mock_team

    with pytest.raises(RuntimeError, match="Stream crash"):
        async for _ in run_workflow_stream("test task"):
            pass

    mock_client.close.assert_awaited_once()


@patch("app.runner.Console")
@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_cli_run_success(mock_client_class, mock_console):
    mock_client = MockModelClient()
    mock_client.close = AsyncMock()
    mock_client_class.return_value = mock_client

    mock_console.return_value = AsyncMock()

    await run("cli task")

    mock_console.assert_called_once()
    mock_client.close.assert_awaited_once()


@patch("app.runner.Console")
@patch("app.runner.OllamaChatCompletionClient")
@patch("app.runner.create_team")
@pytest.mark.anyio
async def test_cli_run_failure(mock_create_team, mock_client_class, mock_console):
    mock_client = MockModelClient()
    mock_client.close = AsyncMock()
    mock_client_class.return_value = mock_client

    mock_team = MagicMock()
    mock_team.run_stream = MagicMock(side_effect=RuntimeError("CLI crash"))
    mock_create_team.return_value = mock_team

    with pytest.raises(RuntimeError, match="CLI crash"):
        await run("cli task")

    mock_client.close.assert_awaited_once()
