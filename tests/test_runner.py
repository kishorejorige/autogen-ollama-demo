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
            content="Mock agent output. Review status: APPROVED\nTest status: PASS",
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

    assert len(participants) == 5

    names = [agent.name for agent in participants]
    assert names == [
        "manager_agent",
        "python_developer",
        "code_reviewer",
        "tester_agent",
        "documentation_agent",
    ]

    for agent in participants:
        assert isinstance(agent, AssistantAgent)

    assert kwargs.get("max_turns") == 5


@patch("app.runner.create_documentation_agent")
@patch("app.runner.create_tester_agent")
@patch("app.runner.create_code_reviewer_agent")
@patch("app.runner.create_python_developer_agent")
@patch("app.runner.create_manager_agent")
def test_agent_factories_called_in_order(
    mock_manager, mock_developer, mock_reviewer, mock_tester, mock_documenter
):
    call_order = []

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
    mock_tester.side_effect = lambda *args, **kwargs: (
        call_order.append("tester"),
        MagicMock(),
    )[1]
    mock_documenter.side_effect = lambda *args, **kwargs: (
        call_order.append("documenter"),
        MagicMock(),
    )[1]

    client = MockModelClient()
    create_team(client)

    assert call_order == ["manager", "developer", "reviewer", "tester", "documenter"]


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
    assert serialized["metadata"] == {"stop_reason": "Max turns reached", "iteration": 1}


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
    assert serialized["metadata"] == {"iteration": 1}


@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_streaming_agent_sources(mock_client_class):
    mock_client_class.return_value = MockModelClient()

    events = []
    async for event in run_workflow_stream("Do something"):
        events.append(event)

    assert len(events) > 0
    assert events[0]["event_type"] == "workflow_started"
    assert any(e.get("event_type") == "workflow_completed" for e in events)


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


def test_status_parsing():
    from app.runner import parse_reviewer_status, parse_tester_status
    assert parse_reviewer_status("some text Review status: APPROVED more text") == "APPROVED"
    assert parse_reviewer_status("some text Review status: CHANGES_REQUIRED") == "CHANGES_REQUIRED"
    assert parse_reviewer_status("no status") == "CHANGES_REQUIRED"

    assert parse_tester_status("some text Test status: PASS more text") == "PASS"
    assert parse_tester_status("some text Test status: FAIL") == "FAIL"
    assert parse_tester_status("no status") == "FAIL"


def test_file_extraction():
    from app.runner import extract_generated_files
    messages = [
        {"source": "manager_agent", "content": "```python\n# skip.py\nprint(1)\n```"},
        {"source": "python_developer", "content": "Here is the code:\n```python\n# app/main.py\ndef hello():\n    pass\n```\nAnd a test file:\n```py\n# tests/test_hello.py\ndef test():\n    pass\n```"}
    ]
    files = extract_generated_files(messages, iteration=1)
    assert len(files) == 2
    assert files[0]["filename"] == "app/main.py"
    assert "def hello():" in files[0]["content"]
    assert files[1]["filename"] == "tests/test_hello.py"


class ScenarioModelClient(MockModelClient):
    def __init__(self, scenario="immediate_pass", *args, **kwargs):
        self.scenario = scenario
        self.call_count = 0

    async def create(self, messages, *args, **kwargs):
        self.call_count += 1
        system_content = messages[0].content.lower() if messages else ""

        is_reviewer = "senior python code reviewer" in system_content
        is_tester = "senior qa and testing engineer" in system_content
        is_developer = "senior python developer" in system_content
        is_manager = "manager agent" in system_content
        is_documenter = "technical writer" in system_content
        print(f"\n[create_mock] call={self.call_count} manager={is_manager} developer={is_developer} reviewer={is_reviewer} tester={is_tester} documenter={is_documenter}")

        if is_manager:
            return CreateResult(content="Delegate to developer.", usage=RequestUsage(0,0), finish_reason="stop", cached=False)

        if is_developer:
            return CreateResult(content="```python\n# app.py\nprint('hello')\n```", usage=RequestUsage(0,0), finish_reason="stop", cached=False)

        if is_documenter:
            return CreateResult(content="Here is the documentation.", usage=RequestUsage(0,0), finish_reason="stop", cached=False)

        if self.scenario == "immediate_pass":
            if is_reviewer:
                return CreateResult(
                    content="```json\n{\n  \"status\": \"APPROVED\",\n  \"feedback\": \"Looks good!\"\n}\n```\nReview status: APPROVED",
                    usage=RequestUsage(0,0), finish_reason="stop", cached=False
                )
            if is_tester:
                return CreateResult(
                    content="```json\n{\n  \"status\": \"PASS\",\n  \"summary\": \"All tests passed.\"\n}\n```\nTest status: PASS",
                    usage=RequestUsage(0,0), finish_reason="stop", cached=False
                )

        elif self.scenario == "fail_then_pass":
            if is_reviewer:
                # Fails first review (call count check or we can inspect latest prompt for repair)
                if self.call_count <= 4:
                    return CreateResult(
                        content="```json\n{\n  \"status\": \"CHANGES_REQUIRED\",\n  \"feedback\": \"Add comment.\"\n}\n```\nReview status: CHANGES_REQUIRED",
                        usage=RequestUsage(0,0), finish_reason="stop", cached=False
                    )
                else:
                    return CreateResult(
                        content="```json\n{\n  \"status\": \"APPROVED\",\n  \"feedback\": \"Looks good!\"\n}\n```\nReview status: APPROVED",
                        usage=RequestUsage(0,0), finish_reason="stop", cached=False
                    )
            if is_tester:
                return CreateResult(
                    content="```json\n{\n  \"status\": \"PASS\",\n  \"summary\": \"All tests passed.\"\n}\n```\nTest status: PASS",
                    usage=RequestUsage(0,0), finish_reason="stop", cached=False
                )

        elif self.scenario == "max_retries":
            if is_reviewer:
                return CreateResult(
                    content="```json\n{\n  \"status\": \"CHANGES_REQUIRED\",\n  \"feedback\": \"Add comment.\"\n}\n```\nReview status: CHANGES_REQUIRED",
                    usage=RequestUsage(0,0), finish_reason="stop", cached=False
                )
            if is_tester:
                return CreateResult(
                    content="```json\n{\n  \"status\": \"FAIL\",\n  \"summary\": \"Tests failed.\"\n}\n```\nTest status: FAIL",
                    usage=RequestUsage(0,0), finish_reason="stop", cached=False
                )

        elif self.scenario == "malformed_status":
            if is_reviewer:
                return CreateResult(
                    content="Review status: APPROVED",
                    usage=RequestUsage(0,0), finish_reason="stop", cached=False
                )
            if is_tester:
                return CreateResult(
                    content="Malformed content. Test status: PASS",
                    usage=RequestUsage(0,0), finish_reason="stop", cached=False
                )

        elif self.scenario == "exceptions":
            raise RuntimeError("LLM simulation failure")

        elif self.scenario == "timeout":
            import asyncio
            await asyncio.sleep(0.01)
            return CreateResult(
                content="```json\n{\n  \"status\": \"APPROVED\",\n  \"feedback\": \"Looks good!\"\n}\n```\nReview status: APPROVED",
                usage=RequestUsage(0,0), finish_reason="stop", cached=False
            )

        return CreateResult(content="Default mock output.", usage=RequestUsage(0,0), finish_reason="stop", cached=False)

    async def create_stream(self, *args, **kwargs):
        pass

    @property
    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(vision=False, function_calling=False, json_output=False)

    @property
    def model_info(self):
        return {"vision": False, "family": "unknown"}

    async def close(self):
        pass


@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_scenario_immediate_pass(mock_client_class):
    mock_client_class.return_value = ScenarioModelClient(scenario="immediate_pass")
    events = []
    async for event in run_workflow_stream("Do something"):
        events.append(event)

    assert len(events) > 0
    assert events[0]["event_type"] == "workflow_started"
    completed_evt = next((e for e in events if e.get("event_type") == "workflow_completed"), None)
    assert completed_evt is not None
    state = completed_evt["workflow_state"]
    assert state["status"] == "COMPLETE"
    assert state["current_iteration"] == 1
    assert state["reviewer_status"] == "APPROVED"
    assert state["tester_status"] == "PASS"


@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_scenario_fail_then_pass(mock_client_class):
    mock_client_class.return_value = ScenarioModelClient(scenario="fail_then_pass")
    events = []
    async for event in run_workflow_stream("Do something"):
        events.append(event)

    assert len(events) > 0
    assert any(e.get("event_type") == "repair_started" for e in events)
    completed_evt = next((e for e in events if e.get("event_type") == "workflow_completed"), None)
    assert completed_evt is not None
    state = completed_evt["workflow_state"]
    assert state["status"] == "COMPLETE"
    assert state["current_iteration"] == 2


@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_scenario_max_retries(mock_client_class):
    mock_client_class.return_value = ScenarioModelClient(scenario="max_retries")
    events = []
    async for event in run_workflow_stream("Do something"):
        events.append(event)

    assert len(events) > 0
    attention_evt = next((e for e in events if e.get("event_type") == "workflow_needs_attention"), None)
    assert attention_evt is not None
    state = attention_evt["workflow_state"]
    assert state["status"] == "NEEDS_ATTENTION"
    assert state["current_iteration"] == 3


@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_scenario_malformed_status(mock_client_class):
    mock_client_class.return_value = ScenarioModelClient(scenario="malformed_status")
    events = []
    async for event in run_workflow_stream("Do something"):
        events.append(event)

    assert len(events) > 0
    completed_evt = next((e for e in events if e.get("event_type") == "workflow_completed"), None)
    assert completed_evt is not None
    state = completed_evt["workflow_state"]
    assert state["status"] == "COMPLETE"
    assert state["current_iteration"] == 1


@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_scenario_exceptions(mock_client_class):
    mock_client_class.return_value = ScenarioModelClient(scenario="exceptions")
    events = []
    try:
        async for event in run_workflow_stream("Do something"):
            events.append(event)
    except RuntimeError:
        pass

    assert len(events) > 0
    assert any(e.get("event_type") == "workflow_failed" for e in events)


@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_scenario_timeout(mock_client_class):
    mock_client_class.return_value = ScenarioModelClient(scenario="timeout")
    res = await run_workflow("Do something")
    assert res is not None
    assert "messages" in res


@patch("app.runner.OllamaChatCompletionClient")
@pytest.mark.anyio
async def test_scenario_sse_completion(mock_client_class):
    mock_client_class.return_value = ScenarioModelClient(scenario="immediate_pass")
    events = []
    async for event in run_workflow_stream("Do something"):
        events.append(event)
    assert events[0]["event_type"] == "workflow_started"
    assert events[-1]["event_type"] in ("workflow_completed", "workflow_needs_attention", "workflow_failed")
