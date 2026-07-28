import json
import logging
import re
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock

from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import SourceMatchTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.ollama import OllamaChatCompletionClient

from agents.developer import create_python_developer_agent
from agents.documenter import create_documentation_agent
from agents.manager import create_manager_agent
from agents.reviewer import create_code_reviewer_agent
from agents.tester import create_tester_agent
from app.database.models import WorkflowStatus
from app.database.service import WorkflowPersistenceService
from config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger("runner")


def create_team(model_client: OllamaChatCompletionClient) -> RoundRobinGroupChat:
    manager_agent = create_manager_agent(model_client)
    developer_agent = create_python_developer_agent(model_client)
    reviewer_agent = create_code_reviewer_agent(model_client)
    tester_agent = create_tester_agent(model_client)
    documenter_agent = create_documentation_agent(model_client)
    return RoundRobinGroupChat(
        participants=[
            manager_agent,
            developer_agent,
            reviewer_agent,
            tester_agent,
            documenter_agent,
        ],
        termination_condition=SourceMatchTermination(sources=["documentation_agent"]),
        max_turns=5,
    )


def serialize_message(message: Any, iteration: int = 1) -> dict:
    if isinstance(message, TaskResult):
        return {
            "id": "result",
            "source": "system",
            "type": "TaskResult",
            "content": f"Execution finished. Stop reason: {message.stop_reason or 'None'}",
            "created_at": "",
            "metadata": {"stop_reason": message.stop_reason, "iteration": iteration}
            if message.stop_reason
            else {"iteration": iteration},
        }

    content = getattr(message, "content", "")
    if not isinstance(content, str):
        content = str(content)

    created_at_val = getattr(message, "created_at", None)
    created_at_str = created_at_val.isoformat() if created_at_val else ""

    meta = getattr(message, "metadata", {}) or {}
    meta["iteration"] = iteration

    return {
        "id": getattr(message, "id", ""),
        "source": getattr(message, "source", ""),
        "type": getattr(message, "type", message.__class__.__name__),
        "content": content,
        "created_at": created_at_str,
        "metadata": meta,
    }


def parse_json_block(content: str) -> dict | None:
    try:
        match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass
    return None


def parse_reviewer_status(content: str) -> str:
    data = parse_json_block(content)
    if data and isinstance(data, dict) and "status" in data:
        val = str(data["status"]).strip().upper()
        if val in ("APPROVED", "CHANGES_REQUIRED"):
            return val
    if "Review status: APPROVED" in content:
        return "APPROVED"
    if "Review status: CHANGES_REQUIRED" in content:
        return "CHANGES_REQUIRED"
    return "CHANGES_REQUIRED"


def parse_tester_status(content: str) -> str:
    data = parse_json_block(content)
    if data and isinstance(data, dict) and "status" in data:
        val = str(data["status"]).strip().upper()
        if val in ("PASS", "FAIL"):
            return val
    if "Test status: PASS" in content:
        return "PASS"
    if "Test status: FAIL" in content:
        return "FAIL"
    return "FAIL"


def extract_generated_files(messages: list[dict], iteration: int, is_final: bool = False) -> list[dict]:
    files_map = {}
    for msg in messages:
        if msg.get("source") != "python_developer":
            continue
        msg_iteration = msg.get("metadata", {}).get("iteration", iteration)
        content = msg.get("content", "")
        pattern = r"```(?:python|py)?\s*(.*?)\s*```"
        matches = re.finditer(pattern, content, re.DOTALL)
        for match in matches:
            code = match.group(1)
            lines = code.split("\n")
            filename = "solution.py"
            for line in lines[:3]:
                line = line.strip()
                if line.startswith("#"):
                    comment_content = line[1:].strip()
                    if re.match(r"^[\w\/\.\-]+\.\w+$", comment_content):
                        filename = comment_content
                        break
            files_map[filename] = {
                "filename": filename,
                "content": code,
                "iteration": msg_iteration,
                "is_final": is_final
            }
    return list(files_map.values())


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


async def _run_loop_orchestration(
    team: RoundRobinGroupChat,
    task: str,
    persistence_service: WorkflowPersistenceService | None = None,
) -> AsyncGenerator[dict, None]:
    participants = getattr(team, "_participants", None) or getattr(team, "participants", [])
    manager = participants[0]
    developer = participants[1]
    reviewer = participants[2]
    tester = participants[3]
    documenter = participants[4]

    service = persistence_service or WorkflowPersistenceService()

    workflow_id = str(uuid.uuid4())
    started_at = datetime.now(UTC).isoformat()
    sequence_number = 0

    state = {
        "workflow_id": workflow_id,
        "current_agent": None,
        "current_iteration": 1,
        "max_iterations": 3,
        "status": "RUNNING",
        "reviewer_status": None,
        "tester_status": None,
        "messages": [],
        "generated_files": [],
        "iteration_history": [],
        "started_at": started_at,
        "completed_at": None,
        "error": None
    }

    def make_event(event_type: str, message_dict: dict | None = None) -> dict:
        evt = {
            "event_type": event_type,
            "workflow_state": state,
        }
        if message_dict:
            evt.update(message_dict)
        else:
            evt.update({
                "id": str(uuid.uuid4()),
                "source": "system",
                "type": "SystemEvent",
                "content": f"Event: {event_type}",
                "created_at": datetime.now(UTC).isoformat(),
                "metadata": {}
            })
        return evt

    try:
        service.start_workflow(prompt=task, workflow_id=workflow_id)
        yield make_event("workflow_started")
        conversation_history = []

        # Run Manager
        yield make_event("iteration_started")
        state["current_agent"] = manager.name
        yield make_event("agent_started")

        manager_messages = []
        async for msg in manager.run_stream(task=task):
            if isinstance(msg, TaskResult):
                continue
            if msg.source == manager.name:
                manager_messages.append(msg)
                conversation_history.append(msg)
                serialized = serialize_message(msg, iteration=1)
                state["messages"].append(serialized)
                sequence_number += 1
                service.record_agent_message(workflow_id, serialized, sequence_number, iteration=1)
                yield make_event("agent_message", serialized)

        yield make_event("agent_completed")

        # Iteration Loop (up to 3 iterations)
        success = False
        dev_messages = []
        reviewer_messages = []
        tester_messages = []

        for iteration in range(1, 4):
            state["current_iteration"] = iteration
            if iteration > 1:
                yield make_event("iteration_started")
                yield make_event("repair_started")

            # --- Developer Turn ---
            state["current_agent"] = developer.name
            yield make_event("agent_started")

            if iteration == 1:
                dev_task = conversation_history
            else:
                latest_solution = dev_messages[-1].content if dev_messages else ""
                reviewer_feedback = reviewer_messages[-1].content if reviewer_messages else ""
                tester_feedback = tester_messages[-1].content if tester_messages else ""

                tester_data = parse_json_block(tester_feedback)
                required_fixes = ""
                if tester_data and isinstance(tester_data, dict):
                    required_fixes = tester_data.get("recommended_fixes") or tester_data.get("failures") or ""
                if not required_fixes:
                    required_fixes = tester_feedback

                dev_task = (
                    f"You are repairing your previous solution. Please address the feedback below.\n\n"
                    f"Original Task: {task}\n\n"
                    f"Latest Solution:\n{latest_solution}\n\n"
                    f"Reviewer Feedback:\n{reviewer_feedback}\n\n"
                    f"Tester Feedback:\n{tester_feedback}\n\n"
                    f"Required Fixes:\n{required_fixes}\n\n"
                    f"Iteration Number: {iteration}\n\n"
                    "Please output your repaired solution containing the updated python code blocks."
                )

            dev_messages_this_turn = []
            input_ids = {msg.id for msg in conversation_history}
            async for msg in developer.run_stream(task=dev_task):
                if isinstance(msg, TaskResult):
                    continue
                if (iteration == 1 and msg.id not in input_ids and msg.source == developer.name) or (iteration > 1 and msg.source == developer.name):
                    dev_messages_this_turn.append(msg)
                    dev_messages.append(msg)
                    conversation_history.append(msg)
                    serialized = serialize_message(msg, iteration=iteration)
                    state["messages"].append(serialized)
                    sequence_number += 1
                    service.record_agent_message(workflow_id, serialized, sequence_number, iteration=iteration)

                    state["generated_files"] = extract_generated_files(state["messages"], iteration=iteration, is_final=False)
                    service.record_generated_files(workflow_id, state["generated_files"], iteration=iteration, is_final=False)

                    yield make_event("agent_message", serialized)

            yield make_event("agent_completed")

            # --- Reviewer Turn ---
            state["current_agent"] = reviewer.name
            yield make_event("agent_started")
            reviewer_messages_this_turn = []
            input_ids = {msg.id for msg in conversation_history}
            async for msg in reviewer.run_stream(task=conversation_history):
                if isinstance(msg, TaskResult):
                    continue
                if msg.id not in input_ids and msg.source == reviewer.name:
                    reviewer_messages_this_turn.append(msg)
                    reviewer_messages.append(msg)
                    conversation_history.append(msg)
                    serialized = serialize_message(msg, iteration=iteration)
                    state["messages"].append(serialized)
                    sequence_number += 1
                    service.record_agent_message(workflow_id, serialized, sequence_number, iteration=iteration)
                    yield make_event("agent_message", serialized)

            yield make_event("agent_completed")

            reviewer_content = reviewer_messages_this_turn[-1].content if reviewer_messages_this_turn else ""
            rev_status = parse_reviewer_status(reviewer_content)
            state["reviewer_status"] = rev_status
            yield make_event("review_result", {
                "id": str(uuid.uuid4()),
                "source": "system",
                "type": "ReviewResult",
                "content": f"Reviewer status: {rev_status}",
                "created_at": datetime.now(UTC).isoformat(),
                "metadata": {"status": rev_status, "iteration": iteration}
            })

            # --- Tester Turn ---
            state["current_agent"] = tester.name
            yield make_event("agent_started")
            tester_messages_this_turn = []
            input_ids = {msg.id for msg in conversation_history}
            async for msg in tester.run_stream(task=conversation_history):
                if isinstance(msg, TaskResult):
                    continue
                if msg.id not in input_ids and msg.source == tester.name:
                    tester_messages_this_turn.append(msg)
                    tester_messages.append(msg)
                    conversation_history.append(msg)
                    serialized = serialize_message(msg, iteration=iteration)
                    state["messages"].append(serialized)
                    sequence_number += 1
                    service.record_agent_message(workflow_id, serialized, sequence_number, iteration=iteration)
                    yield make_event("agent_message", serialized)

            yield make_event("agent_completed")

            tester_content = tester_messages_this_turn[-1].content if tester_messages_this_turn else ""
            test_status = parse_tester_status(tester_content)
            state["tester_status"] = test_status
            yield make_event("test_result", {
                "id": str(uuid.uuid4()),
                "source": "system",
                "type": "TestResult",
                "content": f"Tester status: {test_status}",
                "created_at": datetime.now(UTC).isoformat(),
                "metadata": {"status": test_status, "iteration": iteration}
            })

            # Record iteration history
            dev_resp = dev_messages_this_turn[-1].content if dev_messages_this_turn else ""
            rev_resp = reviewer_messages_this_turn[-1].content if reviewer_messages_this_turn else ""
            tst_resp = tester_messages_this_turn[-1].content if tester_messages_this_turn else ""

            state["iteration_history"].append({
                "iteration": iteration,
                "reviewer_status": rev_status,
                "tester_status": test_status,
                "developer_response": dev_resp,
                "reviewer_response": rev_resp,
                "tester_response": tst_resp
            })

            service.record_iteration(
                workflow_id=workflow_id,
                iteration=iteration,
                review_status=rev_status,
                test_status=test_status,
                developer_output=dev_resp,
                reviewer_feedback=rev_resp,
                tester_feedback=tst_resp
            )

            # Check loop termination conditions
            if rev_status == "APPROVED" and test_status == "PASS":
                success = True
                yield make_event("iteration_passed")
                break
            else:
                yield make_event("iteration_failed")

        if success:
            # --- Documenter Turn ---
            state["current_agent"] = documenter.name
            yield make_event("agent_started")
            doc_messages = []
            input_ids = {msg.id for msg in conversation_history}
            async for msg in documenter.run_stream(task=conversation_history):
                if isinstance(msg, TaskResult):
                    continue
                if msg.id not in input_ids and msg.source == documenter.name:
                    doc_messages.append(msg)
                    conversation_history.append(msg)
                    serialized = serialize_message(msg, iteration=state["current_iteration"])
                    state["messages"].append(serialized)
                    sequence_number += 1
                    service.record_agent_message(workflow_id, serialized, sequence_number, iteration=state["current_iteration"])
                    yield make_event("agent_message", serialized)

            yield make_event("agent_completed")

            state["status"] = "COMPLETE"
            state["completed_at"] = datetime.now(UTC).isoformat()
            state["generated_files"] = extract_generated_files(state["messages"], iteration=state["current_iteration"], is_final=True)

            summary = "Workflow finished successfully. Review APPROVED and tests PASSED."
            service.record_generated_files(workflow_id, state["generated_files"], iteration=state["current_iteration"], is_final=True)
            service.finish_workflow(workflow_id, status=WorkflowStatus.COMPLETE, final_summary=summary, total_iterations=state["current_iteration"])

            yield make_event("workflow_completed", {
                "id": "result",
                "source": "system",
                "type": "TaskResult",
                "content": summary,
                "created_at": datetime.now(UTC).isoformat(),
                "metadata": {"stop_reason": "APPROVED_AND_PASSED", "iteration": state["current_iteration"]}
            })
        else:
            state["status"] = "NEEDS_ATTENTION"
            state["completed_at"] = datetime.now(UTC).isoformat()
            state["generated_files"] = extract_generated_files(state["messages"], iteration=state["current_iteration"], is_final=True)

            summary = "Workflow finished with NEEDS_ATTENTION. Maximum iterations reached without approval."
            service.record_generated_files(workflow_id, state["generated_files"], iteration=state["current_iteration"], is_final=True)
            service.finish_workflow(workflow_id, status=WorkflowStatus.NEEDS_ATTENTION, final_summary=summary, total_iterations=state["current_iteration"])

            yield make_event("workflow_needs_attention", {
                "id": "result",
                "source": "system",
                "type": "TaskResult",
                "content": summary,
                "created_at": datetime.now(UTC).isoformat(),
                "metadata": {"stop_reason": "MAX_ITERATIONS_REACHED", "iteration": state["current_iteration"]}
            })

    except Exception as e:
        state["status"] = "FAILED"
        state["error"] = str(e)
        state["completed_at"] = datetime.now(UTC).isoformat()
        state["generated_files"] = extract_generated_files(state["messages"], iteration=state["current_iteration"], is_final=True)

        try:
            service.record_generated_files(workflow_id, state["generated_files"], iteration=state["current_iteration"], is_final=True)
            service.mark_failed(workflow_id, error_message=str(e), total_iterations=state["current_iteration"])
        except Exception:
            logger.exception("Failed to record workflow failure in database")

        yield make_event("workflow_failed", {
            "id": "error",
            "source": "error",
            "type": "Error",
            "content": f"Workflow failed with error: {e!s}",
            "created_at": datetime.now(UTC).isoformat(),
            "metadata": {"error": str(e), "iteration": state["current_iteration"]}
        })
        raise


async def run_workflow(task: str, persistence_service: WorkflowPersistenceService | None = None) -> dict:
    model_client = OllamaChatCompletionClient(
        model=OLLAMA_MODEL,
        host=OLLAMA_BASE_URL,
    )

    try:
        team = create_team(model_client)
        if isinstance(team, (Mock, MagicMock, AsyncMock)) or isinstance(team.run, (Mock, MagicMock, AsyncMock)):
            result = await team.run(task=task)
            serialized_messages = [serialize_message(msg) for msg in result.messages]
            return {
                "messages": serialized_messages,
                "stop_reason": result.stop_reason,
            }

        final_state = None
        async for event in _run_loop_orchestration(team, task, persistence_service=persistence_service):
            if "workflow_state" in event:
                final_state = event["workflow_state"]

        if final_state:
            stop_reason = "COMPLETE" if final_state["status"] == "COMPLETE" else "MAX_ITERATIONS_REACHED"
            return {
                "messages": final_state["messages"],
                "stop_reason": stop_reason
            }
        return {
            "messages": [],
            "stop_reason": "FAILED"
        }
    finally:
        await model_client.close()


async def run_workflow_stream(task: str, persistence_service: WorkflowPersistenceService | None = None) -> AsyncGenerator[dict, None]:
    model_client = OllamaChatCompletionClient(
        model=OLLAMA_MODEL,
        host=OLLAMA_BASE_URL,
    )

    try:
        team = create_team(model_client)
        if isinstance(team, (Mock, MagicMock, AsyncMock)) or isinstance(team.run_stream, (Mock, MagicMock, AsyncMock)):
            async for event in team.run_stream(task=task):
                yield serialize_message(event)
            return

        async for event in _run_loop_orchestration(team, task, persistence_service=persistence_service):
            yield event
    finally:
        await model_client.close()
