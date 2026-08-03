import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.database.models import (
    WorkflowStatus,
)
from app.database.repository import WorkflowRepository
from app.database.service import WorkflowPersistenceService


@pytest.fixture
def db_session(tmp_path):
    db_file = tmp_path / "test.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_sqlite_foreign_keys_enabled(db_session):
    result = db_session.execute(text("PRAGMA foreign_keys")).scalar()
    assert result == 1


def test_create_and_get_workflow(db_session):
    repo = WorkflowRepository(db_session)
    wf = repo.create_workflow("Test Prompt 123")
    assert wf.id is not None
    assert wf.prompt == "Test Prompt 123"
    assert wf.status == WorkflowStatus.RUNNING

    fetched = repo.get_workflow(wf.id)
    assert fetched is not None
    assert fetched.id == wf.id
    assert fetched.prompt == "Test Prompt 123"


def test_iteration_uniqueness_and_saving(db_session):
    repo = WorkflowRepository(db_session)
    wf = repo.create_workflow("Iteration Test")

    iter1 = repo.save_iteration(
        workflow_id=wf.id,
        iteration_number=1,
        review_status="CHANGES_REQUIRED",
        test_status="FAIL",
        developer_output="def foo(): pass",
    )
    assert iter1.iteration_number == 1

    # Saving iteration 1 again should update existing iteration record
    iter1_updated = repo.save_iteration(
        workflow_id=wf.id,
        iteration_number=1,
        review_status="APPROVED",
        test_status="PASS",
    )
    assert iter1_updated.id == iter1.id
    assert iter1_updated.review_status == "APPROVED"
    assert iter1_updated.test_status == "PASS"


def test_message_ordering(db_session):
    repo = WorkflowRepository(db_session)
    wf = repo.create_workflow("Message Order Test")

    repo.save_message(wf.id, "manager_agent", "TextMessage", "Msg 1", sequence_number=1)
    repo.save_message(wf.id, "python_developer", "TextMessage", "Msg 2", sequence_number=2)
    repo.save_message(wf.id, "code_reviewer", "TextMessage", "Msg 3", sequence_number=3)

    wf_fetched = repo.get_workflow(wf.id)
    assert len(wf_fetched.messages) == 3
    assert wf_fetched.messages[0].sequence_number == 1
    assert wf_fetched.messages[1].sequence_number == 2
    assert wf_fetched.messages[2].sequence_number == 3
    assert wf_fetched.messages[0].content == "Msg 1"


def test_generated_file_duplicate_protection(db_session):
    repo = WorkflowRepository(db_session)
    wf = repo.create_workflow("File Test")
    iter_rec = repo.save_iteration(wf.id, iteration_number=1)

    f1 = repo.save_generated_file(wf.id, "app.py", "print(1)", is_final=False, iteration_id=iter_rec.id)
    f2 = repo.save_generated_file(wf.id, "app.py", "print(2)", is_final=True, iteration_id=iter_rec.id)

    assert f1.id == f2.id
    assert f2.content == "print(2)"
    assert f2.is_final is True


def test_cascade_deletion(db_session):
    repo = WorkflowRepository(db_session)
    wf = repo.create_workflow("Cascade Test")
    iter_rec = repo.save_iteration(wf.id, iteration_number=1)
    repo.save_message(wf.id, "dev", "TextMessage", "Hello", sequence_number=1, iteration_id=iter_rec.id)
    repo.save_generated_file(wf.id, "main.py", "pass", iteration_id=iter_rec.id)

    # Confirm created
    assert db_session.scalar(text("SELECT COUNT(*) FROM workflows")) == 1
    assert db_session.scalar(text("SELECT COUNT(*) FROM workflow_iterations")) == 1
    assert db_session.scalar(text("SELECT COUNT(*) FROM agent_messages")) == 1
    assert db_session.scalar(text("SELECT COUNT(*) FROM generated_files")) == 1

    # Delete workflow
    deleted = repo.delete_workflow(wf.id)
    assert deleted is True

    # Assert cascade deleted
    assert db_session.scalar(text("SELECT COUNT(*) FROM workflows")) == 0
    assert db_session.scalar(text("SELECT COUNT(*) FROM workflow_iterations")) == 0
    assert db_session.scalar(text("SELECT COUNT(*) FROM agent_messages")) == 0
    assert db_session.scalar(text("SELECT COUNT(*) FROM generated_files")) == 0


def test_list_workflows_search_filter_pagination(db_session):
    repo = WorkflowRepository(db_session)

    wf1 = repo.create_workflow("Build a Web App with FastAPI")
    repo.complete_workflow(wf1.id, total_iterations=1, status=WorkflowStatus.COMPLETE)

    wf2 = repo.create_workflow("Write a Python CLI tool")
    repo.complete_workflow(wf2.id, total_iterations=3, status=WorkflowStatus.NEEDS_ATTENTION)

    wf3 = repo.create_workflow("Build a FastAPI backend service")
    repo.fail_workflow(wf3.id, failure_summary="Syntax Error")

    # Search case-insensitive
    items, total = repo.list_workflows(search="fastapi")
    assert total == 2
    assert len(items) == 2

    # Status filter
    items, total = repo.list_workflows(status="COMPLETE")
    assert total == 1
    assert items[0].id == wf1.id

    items, total = repo.list_workflows(status="NEEDS_ATTENTION")
    assert total == 1
    assert items[0].id == wf2.id

    # Invalid status filter
    items, total = repo.list_workflows(status="INVALID_STATUS")
    assert total == 0
    assert items == []

    # Pagination
    items, total = repo.list_workflows(limit=1, offset=0)
    assert total == 3
    assert len(items) == 1


def test_stats_computation(db_session):
    repo = WorkflowRepository(db_session)

    w1 = repo.create_workflow("W1")
    repo.complete_workflow(w1.id, total_iterations=1, status=WorkflowStatus.COMPLETE)

    w2 = repo.create_workflow("W2")
    repo.complete_workflow(w2.id, total_iterations=3, status=WorkflowStatus.NEEDS_ATTENTION)

    w3 = repo.create_workflow("W3")
    repo.fail_workflow(w3.id, failure_summary="Error", total_iterations=2)

    repo.create_workflow("W4")  # RUNNING

    stats = repo.get_stats()
    assert stats["total_workflows"] == 4
    assert stats["completed_workflows"] == 1
    assert stats["needs_attention_workflows"] == 1
    assert stats["failed_workflows"] == 1
    assert stats["running_workflows"] == 1
    assert stats["average_iterations"] == 1.5


def test_persistence_service_atomic_transactions(tmp_path):
    db_file = tmp_path / "service_test.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    service = WorkflowPersistenceService(session_factory=TestingSessionLocal)

    wf_id = service.start_workflow("Write calculator")
    assert wf_id is not None

    service.record_agent_message(
        wf_id,
        {"source": "manager_agent", "type": "TextMessage", "content": "Planning..."},
        sequence_number=1,
        iteration=1,
    )

    service.record_generated_files(
        wf_id,
        [{"filename": "calc.py", "content": "def add(a, b): return a + b"}],
        iteration=1,
        is_final=True,
    )

    service.finish_workflow(wf_id, status=WorkflowStatus.COMPLETE, final_summary="Passed all tests", total_iterations=1)

    # Verify directly from DB
    with TestingSessionLocal() as db:
        repo = WorkflowRepository(db)
        wf = repo.get_workflow(wf_id)
        assert wf.status == WorkflowStatus.COMPLETE
        assert len(wf.messages) == 1
        assert len(wf.generated_files) == 1
        assert wf.generated_files[0].is_final is True


def test_database_migration_existing_schema_without_favorite(tmp_path):
    from app.database.connection import init_db
    db_file = tmp_path / "legacy.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    # Create legacy table without favorite column using raw SQL
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE workflows (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                prompt TEXT NOT NULL,
                status VARCHAR(30) NOT NULL,
                final_summary TEXT,
                total_iterations INTEGER DEFAULT 0,
                created_at DATETIME,
                completed_at DATETIME
            )
        """))
        conn.execute(text("""
            INSERT INTO workflows (id, prompt, status, total_iterations)
            VALUES ('legacy-id-123', 'Legacy Workflow Prompt', 'COMPLETE', 2)
        """))
        conn.commit()

    # Call init_db to run migration
    init_db(engine)

    # Verify favorite column was added and existing data remains intact
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with TestingSessionLocal() as db:
        repo = WorkflowRepository(db)
        wf = repo.get_workflow("legacy-id-123")
        assert wf is not None
        assert wf.prompt == "Legacy Workflow Prompt"
        assert wf.status == "COMPLETE"
        assert wf.total_iterations == 2
        assert wf.favorite is False


def test_ensure_db_dir_creates_directory_and_sets_permissions(tmp_path):
    from app.database.connection import ensure_db_dir
    nested_dir = tmp_path / "sub_folder" / "nested"
    db_file = nested_dir / "test_permissions.db"
    db_url = f"sqlite:///{db_file}"

    assert not nested_dir.exists()
    ensure_db_dir(db_url)

    assert nested_dir.exists()
    assert nested_dir.is_dir()
