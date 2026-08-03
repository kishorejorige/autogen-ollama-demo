
from app.quality_gate import (
    ClaimVerifier,
    EvidenceType,
    FrameworkChecker,
    QualityGateResult,
    QualityGateStatus,
    RequirementStatus,
    deserialize_quality_gate,
    evaluate_quality_gate,
    extract_requirements,
    serialize_quality_gate,
)


def test_extract_requirements_all_features():
    prompt = (
        "Build a full-stack web application with FastAPI backend, Angular frontend, "
        "PostgreSQL database, Docker deployment, GitHub Actions CI, JWT authentication, "
        "CSV import/export, dashboards and charts, unit tests, API documentation, "
        "and complete developer documentation."
    )
    reqs = extract_requirements(prompt)
    req_ids = {r.id for r in reqs}
    expected_ids = {
        "req_fastapi",
        "req_angular",
        "req_postgres",
        "req_docker",
        "req_ci",
        "req_jwt",
        "req_csv",
        "req_charts",
        "req_tests",
        "req_api_docs",
        "req_dev_docs",
    }
    assert expected_ids.issubset(req_ids)


def test_framework_checker_detects_flask_substitution():
    prompt = "Build a FastAPI backend app"
    code_content = "from flask import Flask, jsonify\napp = Flask(__name__)"
    results, mismatches = FrameworkChecker.check_frameworks(prompt, code_content)

    assert any(m for m in mismatches if "Flask" in m and "FastAPI" in m)
    assert "req_fastapi" in results
    status, _evidences, _issues = results["req_fastapi"]
    assert status == RequirementStatus.INCORRECT


def test_framework_checker_detects_angular_missing():
    prompt = "Build an Angular app"
    code_content = "console.log('HTML and Vanilla JS only')"
    results, _mismatches = FrameworkChecker.check_frameworks(prompt, code_content)

    assert "req_angular" in results
    status, _evidences, _issues = results["req_angular"]
    assert status == RequirementStatus.MISSING


def test_framework_checker_detects_postgres_substitution():
    prompt = "Build a PostgreSQL app"
    code_content = "import sqlite3\nsqlite:///"
    results, mismatches = FrameworkChecker.check_frameworks(prompt, code_content)

    assert any("PostgreSQL" in m for m in mismatches)
    assert "req_postgres" in results
    status, _evidences, _issues = results["req_postgres"]
    assert status == RequirementStatus.INCORRECT


def test_claim_verifier_flags_unsupported_production_ready():
    content = "This application is production-ready and fully scalable."
    unsupported, prod_ready = ClaimVerifier.verify_claims(
        text_content=content,
        execution_evidence=EvidenceType.MISSING,
        missing_reqs=["req_fastapi", "req_angular"],
    )
    assert len(unsupported) > 0
    assert prod_ready is False


def test_claim_verifier_flags_unsupported_all_tests_passed_when_not_executed():
    content = "All tests passed successfully!"
    unsupported, prod_ready = ClaimVerifier.verify_claims(
        text_content=content,
        execution_evidence=EvidenceType.MISSING,
        missing_reqs=[],
    )
    assert any("tests passed" in c.lower() for c in unsupported)
    assert prod_ready is False


def test_claim_verifier_allows_all_tests_passed_when_executed_and_passed():
    content = "All tests passed successfully!"
    unsupported, prod_ready = ClaimVerifier.verify_claims(
        text_content=content,
        execution_evidence=EvidenceType.EXECUTED_PASSED,
        missing_reqs=[],
    )
    assert not any("tests passed" in c.lower() for c in unsupported)
    assert prod_ready is True


def test_evaluate_quality_gate_deterministic_override_validator_pass():
    prompt = "Build a FastAPI backend with PostgreSQL database"
    content = "from flask import Flask\nimport sqlite3\n# Production-ready solution!\nAll tests passed."
    validator_json = {
        "overall_status": "PASS",
        "requirements": [
            {"name": "FastAPI Framework", "status": "IMPLEMENTED", "evidence": ["CODE_PRESENT"]}
        ],
    }

    result = evaluate_quality_gate(
        prompt=prompt,
        all_messages_content=content,
        tester_status="PASS",
        validator_json=validator_json,
    )

    # Deterministic FrameworkChecker + ClaimVerifier must override validator PASS to FAIL
    assert result.overall_status == QualityGateStatus.FAIL
    assert len(result.framework_mismatches) > 0
    assert len(result.unsupported_claims) > 0
    assert result.production_ready_eligible is False


def test_evaluate_quality_gate_tester_fail_overrides_validator_pass():
    prompt = "Build a simple Python API"
    content = "def app(): pass"
    validator_json = {"overall_status": "PASS", "requirements": []}

    result = evaluate_quality_gate(
        prompt=prompt,
        all_messages_content=content,
        tester_status="FAIL",
        validator_json=validator_json,
    )

    assert result.overall_status == QualityGateStatus.FAIL


def test_evaluate_quality_gate_genuine_pass():
    prompt = "Build a FastAPI backend with PostgreSQL"
    content = (
        "from fastapi import FastAPI\n"
        "import psycopg2\n"
        "# Verified implementation with tests\n"
        "def test_api(): assert True"
    )
    validator_json = {"overall_status": "PASS", "requirements": []}

    result = evaluate_quality_gate(
        prompt=prompt,
        all_messages_content=content,
        tester_status="PASS",
        validator_json=validator_json,
    )

    assert result.overall_status == QualityGateStatus.PASS


def test_serialize_and_deserialize_quality_gate():
    qg = QualityGateResult(
        overall_status=QualityGateStatus.PASS,
        framework_mismatches=[],
        unsupported_claims=[],
        production_ready_eligible=True,
    )
    serialized = serialize_quality_gate(qg)
    assert isinstance(serialized, str)

    deserialized = deserialize_quality_gate(serialized)
    assert deserialized.overall_status == QualityGateStatus.PASS
    assert deserialized.production_ready_eligible is True


def test_deserialize_quality_gate_handles_legacy_null_and_malformed():
    des1 = deserialize_quality_gate(None)
    assert des1.overall_status == QualityGateStatus.UNKNOWN

    des2 = deserialize_quality_gate("")
    assert des2.overall_status == QualityGateStatus.UNKNOWN

    des3 = deserialize_quality_gate("invalid json string {bad:")
    assert des3.overall_status == QualityGateStatus.UNKNOWN
