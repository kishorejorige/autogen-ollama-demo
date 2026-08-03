import io
import json
import zipfile

from app.database.models import (
    GeneratedFile,
    Workflow,
    WorkflowIteration,
)
from app.export_service import ExportService
from app.project_validator import (
    RunReadiness,
    ValidationStatus,
    validate_project_artifacts,
)
from app.quality_gate import (
    QualityGateStatus,
    deserialize_quality_gate,
    evaluate_quality_gate,
)


def test_local_import_resolves_pass():
    files = {
        "models.py": "class User:\n    pass\n",
        "main.py": "from models import User\n\nuser = User()\n",
    }
    result = validate_project_artifacts(files, prompt="Build Python API")
    assert "Unresolved import 'from models'" not in result.unresolved_imports
    assert result.syntax_errors == []


def test_missing_models_py_fail():
    files = {
        "main.py": "from models import User\n\nuser = User()\n",
    }
    result = validate_project_artifacts(files, prompt="Build Python API")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("models" in imp for imp in result.unresolved_imports)


def test_missing_database_py_fail():
    files = {
        "models.py": "class User:\n    pass\n",
        "main.py": "from database import SessionLocal\n\ndb = SessionLocal()\n",
    }
    result = validate_project_artifacts(files, prompt="Build Python API")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("database" in imp for imp in result.unresolved_imports)


def test_undefined_get_user_fail():
    files = {
        "main.py": "def login():\n    u = get_user('admin')\n    return u\n",
    }
    result = validate_project_artifacts(files, prompt="Build Python API")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("get_user" in sym for sym in result.undefined_symbols)


def test_undefined_verify_password_fail():
    files = {
        "main.py": "def auth():\n    v = verify_password('p', 'h')\n    return v\n",
    }
    result = validate_project_artifacts(files, prompt="Build Python API")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("verify_password" in sym for sym in result.undefined_symbols)


def test_missing_todo_user_id_attribute_fail():
    files = {
        "models.py": "class Todo:\n    title: str\n",
        "main.py": "from models import Todo\ndef get_todos():\n    return Todo.user_id\n",
    }
    result = validate_project_artifacts(files, prompt="Build Python API")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("user_id" in attr for attr in result.missing_model_attributes)


def test_top_level_fastapi_folder_shadowing_fail():
    files = {
        "fastapi/app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        "requirements.txt": "fastapi\nuvicorn\n",
    }
    result = validate_project_artifacts(files, prompt="Build FastAPI app")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("fastapi" in conf for conf in result.module_conflicts)


def test_backend_folder_fastapi_pass():
    files = {
        "backend/models.py": "class Todo:\n    id: int\n",
        "backend/database.py": "class SessionLocal:\n    pass\n",
        "backend/main.py": "from fastapi import FastAPI\nfrom backend.models import Todo\napp = FastAPI()\n@app.get('/')\ndef root(): return {'ok': True}\n",
        "requirements.txt": "fastapi\nuvicorn\n",
        "README.md": "# Production App\n\n" + "x" * 150,
    }
    result = validate_project_artifacts(files, prompt="Build FastAPI app")
    assert result.module_conflicts == []


def test_placeholder_readme_fail():
    files = {
        "README.md": "# Documentation\n# Add installation instructions and API references",
        "main.py": "print('hello')",
    }
    result = validate_project_artifacts(files, prompt="Build Python app")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("README" in f or "readme" in f for f in result.placeholder_files)


def test_placeholder_source_file_fail():
    files = {
        "solution.py": "# Documentation\n# Add API references and usage instructions",
    }
    result = validate_project_artifacts(files, prompt="Build Python app")
    assert result.overall_status == ValidationStatus.FAIL
    assert "solution.py" in result.placeholder_files


def test_missing_requirements_or_pyproject_fail():
    files = {
        "main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
    }
    result = validate_project_artifacts(files, prompt="Build FastAPI backend")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("requirements.txt" in dep for dep in result.missing_dependency_files)


def test_missing_angular_package_json_fail():
    files = {
        "src/main.ts": "console.log('angular')",
    }
    result = validate_project_artifacts(files, prompt="Build Angular app")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("package.json" in dep for dep in result.missing_dependency_files)


def test_missing_angular_method_in_template_fail():
    files = {
        "package.json": "{}",
        "angular.json": "{}",
        "tsconfig.json": "{}",
        "src/main.ts": "console.log('main')",
        "src/app/todo.component.html": "<button (click)=\"deleteTodo(todo.id)\">Delete</button>",
        "src/app/todo.component.ts": "export class TodoComponent {\n  getTodos() {}\n}\n",
    }
    result = validate_project_artifacts(files, prompt="Build Angular app")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("deleteTodo" in issue for issue in result.frontend_issues)


def test_placeholder_angular_api_url_fail():
    files = {
        "package.json": "{}",
        "angular.json": "{}",
        "tsconfig.json": "{}",
        "src/main.ts": "const url = 'http://your-api-url/api';",
    }
    result = validate_project_artifacts(files, prompt="Build Angular app")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("your-api-url" in r for r in result.placeholder_reasons)


def test_invalid_migration_syntax_fail():
    files = {
        "migrations/env.py": "def run_migrations():\n    if True\n        print('invalid')\n",
    }
    result = validate_project_artifacts(files, prompt="Build Python app with migrations")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("migrations/env.py" in err for err in result.syntax_errors)


def test_fastapi_app_test_client_fail():
    files = {
        "main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        "test_main.py": "from main import app\nclient = app.test_client()\n",
        "requirements.txt": "fastapi\nuvicorn\n",
    }
    result = validate_project_artifacts(files, prompt="Build FastAPI app")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("app.test_client()" in issue for issue in result.backend_issues)


def test_hardcoded_jwt_secret_fail():
    files = {
        "main.py": "from fastapi import FastAPI\nSECRET_KEY = \"your-secret-key\"\napp = FastAPI()\n",
        "requirements.txt": "fastapi\nuvicorn\n",
    }
    result = validate_project_artifacts(files, prompt="Build FastAPI app with JWT")
    assert result.overall_status == ValidationStatus.FAIL
    assert any("your-secret-key" in sec for sec in result.security_issues)


def test_github_actions_without_tests_fail():
    files = {
        "main.py": "print(1)\n",
    }
    result = validate_project_artifacts(files, prompt="Build app with GitHub Actions CI")
    assert result.overall_status == ValidationStatus.FAIL
    assert any(".github/workflows/ci.yml" in dep for dep in result.missing_dependency_files)


def test_docker_cmd_missing_module_fail():
    files = {
        "Dockerfile": "FROM python:3.12\nCMD [\"python\", \"nonexistent_main.py\"]\n",
    }
    result = validate_project_artifacts(files, prompt="Build Python app with Docker")
    assert result.overall_status == ValidationStatus.FAIL


def test_contradictory_pass_and_not_executed_fail():
    qg = evaluate_quality_gate(
        prompt="Build FastAPI + PostgreSQL Todo app",
        all_messages_content="All tests passed. Fully implemented production-ready.",
        tester_status="PASS",
        tester_execution_evidence="NOT_EXECUTED",
        dev_content="from fastapi import FastAPI\napp = FastAPI()\n",
        generated_files=[{"filename": "main.py", "content": "from fastapi import FastAPI\napp = FastAPI()\n"}],
    )
    assert qg.overall_status == QualityGateStatus.FAIL
    assert any("Claimed 'tests passed'" in claim for claim in qg.unsupported_claims)


def test_valid_compact_project_pass():
    files = {
        "models.py": "class Todo:\n    id: int\n    title: str\n",
        "database.py": "class SessionLocal:\n    pass\n",
        "main.py": "from fastapi import FastAPI\nfrom models import Todo\nfrom database import SessionLocal\napp = FastAPI()\n@app.get('/')\ndef index(): return {'ok': True}\n",
        "requirements.txt": "fastapi\nuvicorn\npsycopg2-binary\n",
        "Dockerfile": "FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nCMD [\"uvicorn\", \"main:app\"]\n",
        "docker-compose.yml": "services:\n  backend:\n    build: .\n",
        "README.md": "# Todo Backend Project\n\nThis is a complete FastAPI backend project with Docker setup.\n" + "Overview of features.\n" * 10,
    }
    result = validate_project_artifacts(files, prompt="Build FastAPI + PostgreSQL Todo application with Docker")
    assert result.syntax_errors == []
    assert result.unresolved_imports == []
    assert result.undefined_symbols == []
    assert result.module_conflicts == []
    assert result.placeholder_files == []


def test_real_todo_incomplete_failure_regression():
    files = {
        "fastapi/app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        "main.py": "from models import User\nfrom database import SessionLocal\nfrom fastapi import FastAPI\nSECRET_KEY = \"your-secret-key\"\napp = FastAPI()\n@app.get('/user')\ndef user():\n    return get_user('admin')\n@app.post('/login')\ndef login():\n    return verify_password('p', 'h')\n",
        "README.md": "# Documentation\n# Add installation instructions and API references",
        "solution.py": "# Documentation\n# Add API references and usage instructions",
        "migrations/alembic.ini": "[alembic]\nscript_location = alembic\n",
        "migrations/alembic/versions/3a1b2c.py": "def upgrade():\n    if True\n        print('invalid')\n",
        "tests/unit/test_todo.py": "from main import app\ndef test_app():\n    client = app.test_client()\n",
    }
    prompt = "Build a FastAPI + Angular + PostgreSQL Todo application with Docker, GitHub Actions, JWT authentication, unit tests, OpenAPI documentation, and developer documentation."
    result = validate_project_artifacts(files, prompt=prompt)

    assert result.overall_status == ValidationStatus.FAIL
    assert result.run_readiness == RunReadiness.NOT_RUNNABLE
    assert any("models" in imp for imp in result.unresolved_imports)
    assert any("database" in imp for imp in result.unresolved_imports)
    assert any("get_user" in sym for sym in result.undefined_symbols)
    assert any("verify_password" in sym for sym in result.undefined_symbols)
    assert any("fastapi" in conf for conf in result.module_conflicts)
    assert any("README.md" in pf for pf in result.placeholder_files)
    assert any("solution.py" in pf for pf in result.placeholder_files)
    assert any("requirements.txt" in dep for dep in result.missing_dependency_files)
    assert any("package.json" in dep for dep in result.missing_dependency_files)
    assert any("3a1b2c.py" in err for err in result.syntax_errors)


def test_positive_compact_project_regression():
    files = {
        "backend/models.py": "class Todo:\n    id: int\n    user_id: int\n",
        "backend/database.py": "class SessionLocal:\n    pass\n",
        "backend/main.py": "from fastapi import FastAPI\nfrom backend.models import Todo\nfrom backend.database import SessionLocal\napp = FastAPI()\n@app.get('/todos')\ndef get_todos(): return [Todo()]\n",
        "requirements.txt": "fastapi\nuvicorn\npsycopg2-binary\n",
        "package.json": "{\"name\": \"frontend\", \"version\": \"1.0.0\"}\n",
        "angular.json": "{\"projects\": {}}\n",
        "tsconfig.json": "{}\n",
        "src/main.ts": "console.log('Angular App');\n",
        "src/app/todo.component.ts": "export class TodoComponent {\n  deleteTodo(id: number) {}\n}\n",
        "src/app/todo.component.html": "<button (click)=\"deleteTodo(1)\">Delete</button>\n",
        "Dockerfile": "FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nCMD [\"uvicorn\", \"backend.main:app\"]\n",
        "docker-compose.yml": "services:\n  backend:\n    build: .\n",
        ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest\n",
        "README.md": "# Full Production Ready App\n\nArchitecture, prerequisites, installation, env vars, docker and test details.\n" + "Details\n" * 15,
    }
    prompt = "Build a FastAPI + Angular + PostgreSQL Todo application with Docker and GitHub Actions"
    result = validate_project_artifacts(files, prompt=prompt)

    assert result.syntax_errors == []
    assert result.unresolved_imports == []
    assert result.undefined_symbols == []
    assert result.module_conflicts == []
    assert result.placeholder_files == []
    assert result.missing_dependency_files == []


def test_zip_export_includes_iterations_and_quality_report():
    wf = Workflow(
        id="test-wf-zip-1",
        prompt="Build FastAPI app",
        status="NEEDS_ATTENTION",
        total_iterations=2,
        final_summary="Failed after max iterations",
        quality_gate_data=json.dumps({"overall_status": "FAIL", "run_readiness": "NOT_RUNNABLE", "project_validation": {"unresolved_imports": ["models"]}}),
    )
    iter1 = WorkflowIteration(id=1, workflow_id=wf.id, iteration_number=1)
    iter2 = WorkflowIteration(id=2, workflow_id=wf.id, iteration_number=2)
    wf.iterations = [iter1, iter2]

    f1 = GeneratedFile(id="f1", workflow_id=wf.id, iteration_id=1, filename="main.py", content="print(1)", is_final=False)
    f2 = GeneratedFile(id="f2", workflow_id=wf.id, iteration_id=2, filename="main.py", content="print(2)", is_final=True)
    f1.iteration = iter1
    f2.iteration = iter2
    wf.generated_files = [f1, f2]

    zip_bytes = ExportService.export_zip(wf)
    assert len(zip_bytes) > 0

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "quality-report.json" in namelist
        assert "README.md" in namelist
        assert "iterations/iteration-1/main.py" in namelist
        assert "iterations/iteration-2/main.py" in namelist
        assert "final/README.md" in namelist


def test_zip_export_no_accepted_final_when_gate_fails():
    wf = Workflow(
        id="test-wf-fail",
        prompt="Build app",
        status="NEEDS_ATTENTION",
        total_iterations=1,
        quality_gate_data=json.dumps({"overall_status": "FAIL", "run_readiness": "NOT_RUNNABLE", "project_validation": {}}),
    )
    f1 = GeneratedFile(id="f1", workflow_id=wf.id, filename="main.py", content="print(1)", is_final=True)
    wf.generated_files = [f1]

    zip_bytes = ExportService.export_zip(wf)
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "final/README.md" in namelist
        assert "final/main.py" not in namelist


def test_zip_export_accepted_final_when_gate_passes():
    wf = Workflow(
        id="test-wf-pass",
        prompt="Build app",
        status="COMPLETE",
        total_iterations=1,
        quality_gate_data=json.dumps({"overall_status": "PASS", "run_readiness": "RUNNABLE", "project_validation": {}}),
    )
    f1 = GeneratedFile(id="f1", workflow_id=wf.id, filename="main.py", content="print(1)", is_final=True)
    wf.generated_files = [f1]

    zip_bytes = ExportService.export_zip(wf)
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        namelist = zf.namelist()
        assert "final/main.py" in namelist


def test_legacy_quality_data_deserializes_cleanly():
    qg1 = deserialize_quality_gate(None)
    assert qg1.overall_status == QualityGateStatus.UNKNOWN
    assert qg1.run_readiness == RunReadiness.UNKNOWN

    qg2 = deserialize_quality_gate("invalid json string {{{")
    assert qg2.overall_status == QualityGateStatus.UNKNOWN
    assert qg2.run_readiness == RunReadiness.UNKNOWN

    qg3 = deserialize_quality_gate("{}")
    assert qg3.overall_status == QualityGateStatus.UNKNOWN
    assert qg3.run_readiness == RunReadiness.UNKNOWN
