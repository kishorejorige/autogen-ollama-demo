import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.api import app
from app.database.connection import Base, get_db
from app.database.repository import WorkflowRepository


@pytest.fixture
def test_db_session(tmp_path):
    db_file = tmp_path / "api_test.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def api_client(test_db_session):
    return TestClient(app)


def test_list_workflows_empty(api_client):
    response = api_client.get("/api/workflows")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 10
    assert data["offset"] == 0


def test_list_workflows_search_and_filter(api_client, test_db_session):
    with test_db_session() as db:
        repo = WorkflowRepository(db)
        w1 = repo.create_workflow("Create Python Script")
        repo.complete_workflow(w1.id, total_iterations=1, status="COMPLETE")

        w2 = repo.create_workflow("Build Angular Application")
        repo.complete_workflow(w2.id, total_iterations=2, status="NEEDS_ATTENTION")

    # Search prompt
    res = api_client.get("/api/workflows?search=python")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["prompt"] == "Create Python Script"

    # Status filter
    res = api_client.get("/api/workflows?status=NEEDS_ATTENTION")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "NEEDS_ATTENTION"

    # Invalid status filter
    res = api_client.get("/api/workflows?status=INVALID_STATUS")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_workflow_stats_endpoint(api_client, test_db_session):
    with test_db_session() as db:
        repo = WorkflowRepository(db)
        w1 = repo.create_workflow("Task 1")
        repo.complete_workflow(w1.id, total_iterations=1, status="COMPLETE")

        w2 = repo.create_workflow("Task 2")
        repo.fail_workflow(w2.id, failure_summary="Error", total_iterations=2)

    res = api_client.get("/api/workflows/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_workflows"] == 2
    assert data["completed_workflows"] == 1
    assert data["failed_workflows"] == 1
    assert data["needs_attention_workflows"] == 0
    assert data["average_iterations"] == 1.5


def test_workflow_detail_endpoint(api_client, test_db_session):
    with test_db_session() as db:
        repo = WorkflowRepository(db)
        w = repo.create_workflow("Detail Task")
        it = repo.save_iteration(w.id, iteration_number=1, review_status="APPROVED", test_status="PASS")
        repo.save_message(w.id, "manager_agent", "TextMessage", "Plan", sequence_number=1, iteration_id=it.id)
        repo.save_message(w.id, "python_developer", "TextMessage", "Code", sequence_number=2, iteration_id=it.id)
        repo.save_generated_file(w.id, "draft.py", "draft", is_final=False, iteration_id=it.id)
        repo.save_generated_file(w.id, "final.py", "final", is_final=True, iteration_id=it.id)
        repo.complete_workflow(w.id, final_summary="Done", total_iterations=1)
        wf_id = w.id

    res = api_client.get(f"/api/workflows/{wf_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == wf_id
    assert data["prompt"] == "Detail Task"
    assert len(data["iterations"]) == 1
    assert len(data["messages"]) == 2
    assert data["messages"][0]["sequence_number"] == 1
    assert data["messages"][1]["sequence_number"] == 2

    # Generated files: final file first!
    assert len(data["generated_files"]) == 2
    assert data["generated_files"][0]["filename"] == "final.py"
    assert data["generated_files"][0]["is_final"] is True


def test_workflow_detail_not_found(api_client):
    res = api_client.get("/api/workflows/non-existent-id")
    assert res.status_code == 404
    assert res.json()["detail"] == "Workflow not found"


def test_delete_workflow_endpoint(api_client, test_db_session):
    with test_db_session() as db:
        repo = WorkflowRepository(db)
        w = repo.create_workflow("To Delete")
        wf_id = w.id

    # Delete
    res = api_client.delete(f"/api/workflows/{wf_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "deleted"

    # Confirm 404 after deletion
    res_get = api_client.get(f"/api/workflows/{wf_id}")
    assert res_get.status_code == 404


def test_favorite_toggle_endpoints(api_client, test_db_session):
    with test_db_session() as db:
        repo = WorkflowRepository(db)
        w = repo.create_workflow("Fav Task")
        wf_id = w.id

    # Mark favorite
    res = api_client.post(f"/api/workflows/{wf_id}/favorite")
    assert res.status_code == 200
    assert res.json()["favorite"] is True

    # Remove favorite
    res = api_client.delete(f"/api/workflows/{wf_id}/favorite")
    assert res.status_code == 200
    assert res.json()["favorite"] is False

    # 404 for non-existent
    res_post_404 = api_client.post("/api/workflows/non-existent/favorite")
    assert res_post_404.status_code == 404

    res_del_404 = api_client.delete("/api/workflows/non-existent/favorite")
    assert res_del_404.status_code == 404


def test_date_range_filtering_and_validation(api_client, test_db_session):
    with test_db_session() as db:
        repo = WorkflowRepository(db)
        repo.create_workflow("Today Task")

    # Valid ranges
    for rng in ["today", "7d", "30d"]:
        res = api_client.get(f"/api/workflows?date_range={rng}")
        assert res.status_code == 200

    # Invalid range -> 400
    res_invalid = api_client.get("/api/workflows?date_range=invalid_range")
    assert res_invalid.status_code == 400
    assert "Invalid date_range parameter" in res_invalid.json()["detail"]


def test_export_json_endpoint(api_client, test_db_session):
    with test_db_session() as db:
        repo = WorkflowRepository(db)
        w = repo.create_workflow("Export JSON Task")
        it = repo.save_iteration(w.id, iteration_number=1)
        repo.save_message(w.id, "python_developer", "TextMessage", "Code content", sequence_number=1, iteration_id=it.id)
        repo.save_generated_file(w.id, "main.py", "print('hello')", is_final=True, iteration_id=it.id)
        wf_id = w.id

    res = api_client.get(f"/api/workflows/{wf_id}/export/json")
    assert res.status_code == 200
    data = res.json()
    assert "workflow" in data
    assert "iterations" in data
    assert "messages" in data
    assert "generated_files" in data
    assert data["workflow"]["id"] == wf_id
    assert len(data["generated_files"]) == 1

    # 404
    res_404 = api_client.get("/api/workflows/non-existent/export/json")
    assert res_404.status_code == 404


def test_export_zip_endpoint(api_client, test_db_session):
    import io
    import zipfile

    with test_db_session() as db:
        repo = WorkflowRepository(db)
        w = repo.create_workflow("Export ZIP Task")
        repo.save_generated_file(w.id, "app.py", "print('zip test')", is_final=True)
        wf_id = w.id

    res = api_client.get(f"/api/workflows/{wf_id}/export/zip")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    assert f"filename=workflow_{wf_id}.zip" in res.headers["content-disposition"]

    # Verify zip content
    buf = io.BytesIO(res.content)
    with zipfile.ZipFile(buf, "r") as zf:
        namelist = zf.namelist()
        assert "app.py" in namelist
        assert "README.md" in namelist
        assert zf.read("app.py").decode("utf-8") == "print('zip test')"

    # 404
    res_404 = api_client.get("/api/workflows/non-existent/export/zip")
    assert res_404.status_code == 404


def test_updated_stats_with_favorites(api_client, test_db_session):
    with test_db_session() as db:
        repo = WorkflowRepository(db)
        w = repo.create_workflow("Fav Stat Task")
        repo.mark_favorite(w.id)

    res = api_client.get("/api/workflows/stats")
    assert res.status_code == 200
    data = res.json()
    assert "favorite_count" in data
    assert data["favorite_count"] == 1
    assert "average_iterations" in data
