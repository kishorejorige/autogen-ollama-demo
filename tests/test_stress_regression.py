import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import init_db
from app.database.models import WorkflowStatus
from app.database.service import WorkflowPersistenceService
from app.quality_gate import (
    QualityGateStatus,
    deserialize_quality_gate,
)
from app.runner import _run_loop_orchestration


@pytest.fixture
def test_persistence_service():
    engine = create_engine("sqlite:///:memory:")
    init_db(engine)
    session_factory = sessionmaker(bind=engine)
    return WorkflowPersistenceService(session_factory=session_factory)


@pytest.mark.anyio
async def test_bad_flask_regression_scenario(test_persistence_service):
    """
    Stress regression test:
    Validates that a solution substituting Flask for FastAPI, omitting Angular,
    using SQLite instead of PostgreSQL, and claiming 'production-ready' without test evidence
    is REJECTED by the Quality Gate, undergoes bounded repair turns with focused repair context,
    and terminates at status NEEDS_ATTENTION with Quality Gate FAIL.
    """
    prompt = (
        "Build a production-ready full-stack application with FastAPI backend, Angular frontend, "
        "PostgreSQL database, Docker, GitHub Actions CI, JWT authentication, CSV import/export, "
        "dashboards and charts, unit tests, API documentation, and developer documentation."
    )

    flask_developer_output = """
```python
# app.py
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
import sqlite3

app = Flask(__name__)
jwt = JWTManager(app)

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

# Production-ready solution! All tests passed successfully.
```
"""

    validator_non_compliant_json = """
```json
{
  "overall_status": "FAIL",
  "requirements": [
    {
      "name": "FastAPI Framework",
      "status": "INCORRECT",
      "evidence": ["CODE_PRESENT"],
      "issues": ["Flask substituted for FastAPI"]
    },
    {
      "name": "Angular Frontend",
      "status": "MISSING",
      "evidence": ["MISSING"],
      "issues": ["Angular frontend omitted"]
    }
  ],
  "framework_mismatches": ["FastAPI requested but Flask framework used"],
  "missing_deliverables": ["Angular Frontend"],
  "unsupported_claims": ["Claimed production-ready without evidence"],
  "recommended_fixes": ["Replace Flask with FastAPI", "Implement Angular frontend"]
}
```
"""

    reviewer_changes_required = """
Feedback: Implementation substituted Flask for FastAPI and omitted Angular frontend.
Review status: CHANGES_REQUIRED
"""

    tester_fail_output = """
```json
{
  "status": "FAIL",
  "execution_evidence": "NOT_EXECUTED",
  "summary": "Tests were not executed and framework mismatch found",
  "failures": ["Flask used instead of FastAPI", "Angular missing"],
  "recommended_fixes": ["Use FastAPI", "Add Angular components"]
}
```
Test status: FAIL
"""

    documenter_output = """
Documentation summary: Solution requires attention due to missing Angular components and framework mismatch.
Status: NEEDS_ATTENTION
"""

    def create_mock_agent(name, response_text):
        agent = MagicMock()
        agent.name = name

        async def fake_stream(task):
            msg = MagicMock()
            msg.id = str(uuid.uuid4())
            msg.source = name
            msg.type = "TextMessage"
            msg.content = response_text
            yield msg

        agent.run_stream = MagicMock(side_effect=fake_stream)
        return agent

    manager_agent = create_mock_agent("manager_agent", "Plan: Implement features.")
    dev_agent = create_mock_agent("python_developer", flask_developer_output)
    val_agent = create_mock_agent("requirements_validator", validator_non_compliant_json)
    rev_agent = create_mock_agent("code_reviewer", reviewer_changes_required)
    tst_agent = create_mock_agent("tester_agent", tester_fail_output)
    doc_agent = create_mock_agent("documentation_agent", documenter_output)

    mock_team = MagicMock()
    mock_team._participants = [manager_agent, dev_agent, val_agent, rev_agent, tst_agent, doc_agent]

    events = []
    async for evt in _run_loop_orchestration(mock_team, prompt, test_persistence_service):
        events.append(evt)

    # Verify SSE event sequence
    event_types = [e.get("event_type") for e in events]
    assert "requirements_extracted" in event_types
    assert "requirements_validation_started" in event_types
    assert "requirements_validation_completed" in event_types
    assert "compliance_failed" in event_types
    assert "quality_gate_failed" in event_types
    assert "workflow_needs_attention" in event_types

    # Verify iteration count bounded to 3
    final_event = events[-1]
    workflow_state = final_event["workflow_state"]
    assert workflow_state["status"] == "NEEDS_ATTENTION"
    assert workflow_state["current_iteration"] == 3

    # Verify DB persistence
    wf_id = workflow_state["workflow_id"]
    with test_persistence_service.session_factory() as db:
        from app.database.repository import WorkflowRepository
        repo = WorkflowRepository(db)
        wf = repo.get_workflow(wf_id)
        assert wf is not None
        assert wf.status == WorkflowStatus.NEEDS_ATTENTION

        # Verify Quality Gate data in DB
        qg = deserialize_quality_gate(wf.quality_gate_data)
        assert qg.overall_status == QualityGateStatus.FAIL
        assert len(qg.framework_mismatches) > 0
        assert any("Flask" in m for m in qg.framework_mismatches)
        assert any("req_angular" in m or "Angular" in m for m in qg.missing_deliverables)
        assert len(qg.unsupported_claims) > 0
        assert qg.production_ready_eligible is False


@pytest.mark.anyio
async def test_positive_compliant_completion_scenario(test_persistence_service):
    """
    Positive regression test:
    Validates that a genuinely compliant solution (FastAPI, Angular TypeScript,
    PostgreSQL psycopg2, Dockerfile, GitHub Actions workflow, unit tests)
    passes the Quality Gate and reaches status COMPLETE with Quality Gate PASS.
    """
    prompt = (
        "Build a FastAPI backend with Angular frontend, PostgreSQL database, "
        "Docker deployment, and GitHub Actions CI."
    )

    compliant_developer_output = """
```python
# app/main.py
from fastapi import FastAPI
import psycopg2

app = FastAPI()

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

```text
# requirements.txt
fastapi
uvicorn
psycopg2-binary
```

```json
// package.json
{
  "name": "frontend",
  "version": "1.0.0"
}
```

```json
// angular.json
{
  "projects": {}
}
```

```json
// tsconfig.json
{}
```

```typescript
// src/main.ts
console.log('main');
```

```typescript
// frontend/src/app/app.component.ts
import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  template: '<h1>Angular App</h1>'
})
export class AppComponent {}
```

```dockerfile
# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . /app
```

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
```

```python
# tests/test_api.py
def test_health():
    assert True
```
"""

    validator_pass_json = """
```json
{
  "overall_status": "PASS",
  "requirements": [
    {"name": "FastAPI Framework", "status": "IMPLEMENTED", "evidence": ["CODE_PRESENT"]},
    {"name": "Angular Frontend", "status": "IMPLEMENTED", "evidence": ["CODE_PRESENT"]},
    {"name": "PostgreSQL Database", "status": "IMPLEMENTED", "evidence": ["CONFIG_PRESENT"]},
    {"name": "Docker", "status": "IMPLEMENTED", "evidence": ["FILE_PRESENT"]},
    {"name": "GitHub Actions", "status": "IMPLEMENTED", "evidence": ["CONFIG_PRESENT"]}
  ],
  "framework_mismatches": [],
  "missing_deliverables": [],
  "unsupported_claims": [],
  "recommended_fixes": []
}
```
"""

    reviewer_approved = """
Reviewer summary: All requested components are correctly implemented.
Review status: APPROVED
"""

    tester_pass_output = """
```json
{
  "status": "PASS",
  "execution_evidence": "EXECUTED_PASSED",
  "summary": "All unit tests passed",
  "test_cases": ["test_health"],
  "failures": [],
  "recommended_fixes": []
}
```
Test status: PASS
"""

    documenter_output = """
Documentation summary: Complete and verified solution.
Status: COMPLETE
"""

    def create_mock_agent(name, response_text):
        agent = MagicMock()
        agent.name = name

        async def fake_stream(task):
            msg = MagicMock()
            msg.id = str(uuid.uuid4())
            msg.source = name
            msg.type = "TextMessage"
            msg.content = response_text
            yield msg

        agent.run_stream = MagicMock(side_effect=fake_stream)
        return agent

    manager_agent = create_mock_agent("manager_agent", "Plan: Build compliant solution.")
    dev_agent = create_mock_agent("python_developer", compliant_developer_output)
    val_agent = create_mock_agent("requirements_validator", validator_pass_json)
    rev_agent = create_mock_agent("code_reviewer", reviewer_approved)
    tst_agent = create_mock_agent("tester_agent", tester_pass_output)
    doc_agent = create_mock_agent("documentation_agent", documenter_output)

    mock_team = MagicMock()
    mock_team._participants = [manager_agent, dev_agent, val_agent, rev_agent, tst_agent, doc_agent]

    events = []
    async for evt in _run_loop_orchestration(mock_team, prompt, test_persistence_service):
        events.append(evt)

    # Verify event sequence for completion
    event_types = [e.get("event_type") for e in events]
    assert "quality_gate_passed" in event_types
    assert "workflow_completed" in event_types

    final_event = events[-1]
    workflow_state = final_event["workflow_state"]
    assert workflow_state["status"] == "COMPLETE"
    assert workflow_state["quality_gate_status"] == "PASS"

    # Verify DB persistence
    wf_id = workflow_state["workflow_id"]
    with test_persistence_service.session_factory() as db:
        from app.database.repository import WorkflowRepository
        repo = WorkflowRepository(db)
        wf = repo.get_workflow(wf_id)
        assert wf is not None
        assert wf.status == WorkflowStatus.COMPLETE

        qg = deserialize_quality_gate(wf.quality_gate_data)
        assert qg.overall_status == QualityGateStatus.PASS
