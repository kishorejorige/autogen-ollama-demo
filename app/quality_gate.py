import json
import logging
from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from app.project_validator import (
    ProjectValidationResult,
    RunReadiness,
    ValidationStatus,
    validate_project_artifacts,
)

logger = logging.getLogger(__name__)


class RequirementStatus(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    INCORRECT = "INCORRECT"
    UNKNOWN = "UNKNOWN"


class EvidenceType(str, Enum):
    MENTION_ONLY = "MENTION_ONLY"
    IMPORT_PRESENT = "IMPORT_PRESENT"
    CODE_PRESENT = "CODE_PRESENT"
    CONFIG_PRESENT = "CONFIG_PRESENT"
    FILE_PRESENT = "FILE_PRESENT"
    TEST_PRESENT = "TEST_PRESENT"
    EXECUTED_FAILED = "EXECUTED_FAILED"
    EXECUTED_PASSED = "EXECUTED_PASSED"
    NOT_EXECUTED = "NOT_EXECUTED"
    CLAIM_ONLY = "CLAIM_ONLY"
    MISSING = "MISSING"


class QualityGateStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    UNKNOWN = "UNKNOWN"


class ExtractedRequirement(BaseModel):
    id: str
    name: str
    category: str = "general"
    mandatory: bool = True


class RequirementCompliance(BaseModel):
    id: str
    name: str
    status: RequirementStatus
    evidence: list[EvidenceType] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class QualityGateResult(BaseModel):
    overall_status: QualityGateStatus = QualityGateStatus.UNKNOWN
    run_readiness: RunReadiness = RunReadiness.UNKNOWN
    project_validation: ProjectValidationResult = Field(default_factory=ProjectValidationResult)
    requirements: list[RequirementCompliance] = Field(default_factory=list)
    extracted_requirements: list[ExtractedRequirement] = Field(default_factory=list)
    framework_mismatches: list[str] = Field(default_factory=list)
    missing_deliverables: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    security_issues: list[str] = Field(default_factory=list)
    recommended_fixes: list[str] = Field(default_factory=list)
    production_ready_eligible: bool = False


STANDARD_REQUIREMENTS = [
    {"id": "req_fastapi", "name": "FastAPI Framework", "category": "framework", "keywords": ["fastapi"]},
    {"id": "req_angular", "name": "Angular Frontend", "category": "frontend", "keywords": ["angular"]},
    {"id": "req_postgres", "name": "PostgreSQL Database", "category": "database", "keywords": ["postgres", "postgresql"]},
    {"id": "req_docker", "name": "Docker Deployment", "category": "devops", "keywords": ["docker", "dockerfile", "docker-compose"]},
    {"id": "req_ci", "name": "GitHub Actions CI/CD", "category": "devops", "keywords": ["github actions", "ci/cd", "ci", "workflow"]},
    {"id": "req_jwt", "name": "JWT Authentication", "category": "security", "keywords": ["jwt", "bearer", "token"]},
    {"id": "req_csv", "name": "CSV Import/Export", "category": "feature", "keywords": ["csv"]},
    {"id": "req_charts", "name": "Dashboards & Charts", "category": "feature", "keywords": ["dashboard", "chart", "charts"]},
    {"id": "req_tests", "name": "Automated Unit Tests", "category": "testing", "keywords": ["unit test", "pytest", "tests"]},
    {"id": "req_api_docs", "name": "API Documentation", "category": "docs", "keywords": ["api doc", "swagger", "openapi"]},
    {"id": "req_dev_docs", "name": "Developer Documentation", "category": "docs", "keywords": ["developer doc", "readme"]},
]


def extract_requirements(prompt: str) -> list[ExtractedRequirement]:
    prompt_lower = prompt.lower()
    extracted = []
    for req_def in STANDARD_REQUIREMENTS:
        if any(kw in prompt_lower for kw in req_def["keywords"]):
            extracted.append(
                ExtractedRequirement(
                    id=req_def["id"],
                    name=req_def["name"],
                    category=req_def["category"],
                    mandatory=True,
                )
            )
    return extracted


class FrameworkChecker:
    @staticmethod
    def check_frameworks(prompt: str, code_content: str) -> tuple[dict[str, tuple[RequirementStatus, list[EvidenceType], list[str]]], list[str]]:
        prompt_lower = prompt.lower()
        code_lower = code_content.lower()
        results = {}
        mismatches = []

        # FastAPI check
        if "fastapi" in prompt_lower:
            issues = []
            evidences = []
            if any(term in code_lower for term in ["from flask import", "flask_jwt_extended", "flask-limiter", "flask("]):
                mismatches.append("FastAPI requested but Flask framework components were used.")
                issues.append("Flask substitution detected instead of FastAPI")
                status = RequirementStatus.INCORRECT
                evidences.append(EvidenceType.CODE_PRESENT)
            elif "from fastapi import" in code_lower or "fastapi(" in code_lower:
                status = RequirementStatus.IMPLEMENTED
                evidences.append(EvidenceType.IMPORT_PRESENT)
                evidences.append(EvidenceType.CODE_PRESENT)
            elif "fastapi" in code_lower:
                status = RequirementStatus.PARTIAL
                evidences.append(EvidenceType.MENTION_ONLY)
                issues.append("FastAPI mentioned in text/comments but no actual FastAPI app code provided")
            else:
                status = RequirementStatus.MISSING
                evidences.append(EvidenceType.MISSING)
                issues.append("No FastAPI implementation found")
            results["req_fastapi"] = (status, evidences, issues)

        # Angular check
        if "angular" in prompt_lower:
            issues = []
            evidences = []
            has_ts = "@component" in code_lower or "@injectable" in code_lower or ".ts" in code_lower
            if has_ts:
                status = RequirementStatus.IMPLEMENTED
                evidences.append(EvidenceType.CODE_PRESENT)
            elif "angular" in code_lower:
                status = RequirementStatus.PARTIAL
                evidences.append(EvidenceType.MENTION_ONLY)
                issues.append("Angular mentioned in text but no Angular TypeScript components provided")
            else:
                status = RequirementStatus.MISSING
                evidences.append(EvidenceType.MISSING)
                issues.append("Angular frontend implementation is missing")
            results["req_angular"] = (status, evidences, issues)

        # PostgreSQL check
        if "postgres" in prompt_lower or "postgresql" in prompt_lower:
            issues = []
            evidences = []
            has_pg = any(term in code_lower for term in ["psycopg", "asyncpg", "postgresql://", "postgres_"])
            has_sqlite = "sqlite:///" in code_lower
            if has_pg:
                status = RequirementStatus.IMPLEMENTED
                evidences.append(EvidenceType.CONFIG_PRESENT)
            elif has_sqlite:
                status = RequirementStatus.INCORRECT
                evidences.append(EvidenceType.CODE_PRESENT)
                issues.append("PostgreSQL requested but SQLite database URL was provided instead")
                mismatches.append("PostgreSQL requested but SQLite database used")
            elif "postgres" in code_lower:
                status = RequirementStatus.PARTIAL
                evidences.append(EvidenceType.MENTION_ONLY)
                issues.append("PostgreSQL mentioned without driver or connection configuration")
            else:
                status = RequirementStatus.MISSING
                evidences.append(EvidenceType.MISSING)
                issues.append("PostgreSQL database setup missing")
            results["req_postgres"] = (status, evidences, issues)

        # Docker check
        if "docker" in prompt_lower:
            issues = []
            evidences = []
            if ("from " in code_lower and "workdir " in code_lower) or "dockerfile" in code_lower or "docker-compose" in code_lower:
                status = RequirementStatus.IMPLEMENTED
                evidences.append(EvidenceType.FILE_PRESENT)
                evidences.append(EvidenceType.CONFIG_PRESENT)
            elif "docker" in code_lower:
                status = RequirementStatus.PARTIAL
                evidences.append(EvidenceType.MENTION_ONLY)
                issues.append("Docker mentioned without Dockerfile or docker-compose configuration")
            else:
                status = RequirementStatus.MISSING
                evidences.append(EvidenceType.MISSING)
                issues.append("Docker configuration missing")
            results["req_docker"] = (status, evidences, issues)

        # GitHub Actions / CI check
        if any(term in prompt_lower for term in ["github actions", "ci/cd", "ci"]):
            issues = []
            evidences = []
            if "name:" in code_lower and "on:" in code_lower and "jobs:" in code_lower:
                status = RequirementStatus.IMPLEMENTED
                evidences.append(EvidenceType.CONFIG_PRESENT)
            elif "github actions" in code_lower or "workflow" in code_lower:
                status = RequirementStatus.PARTIAL
                evidences.append(EvidenceType.MENTION_ONLY)
                issues.append("GitHub Actions mentioned without workflow YAML definition")
            else:
                status = RequirementStatus.MISSING
                evidences.append(EvidenceType.MISSING)
                issues.append("GitHub Actions CI/CD configuration missing")
            results["req_ci"] = (status, evidences, issues)

        return results, mismatches


class ClaimVerifier:
    UNSUPPORTED_PHRASES: ClassVar[list[str]] = [
        "fully implemented",
        "production-ready",
        "production ready",
        "all tests passed",
        "tests passed",
        "secure and scalable",
        "complete ci/cd",
        "comprehensive testing",
    ]

    @classmethod
    def verify_claims(
        cls,
        text_content: str,
        execution_evidence: EvidenceType,
        missing_reqs: list[str],
    ) -> tuple[list[str], bool]:
        text_lower = text_content.lower()
        unsupported = []

        # Claim: tests passed
        if (
            any(phrase in text_lower for phrase in ["all tests passed", "tests passed"])
            and execution_evidence != EvidenceType.EXECUTED_PASSED
        ):
            unsupported.append(
                f"Claimed 'tests passed' but execution evidence is {execution_evidence.value} (requires EXECUTED_PASSED)"
            )

        # Claim: production-ready
        if any(phrase in text_lower for phrase in ["production-ready", "production ready", "fully implemented"]):
            if missing_reqs:
                unsupported.append(
                    f"Claimed 'production-ready' / 'fully implemented' while mandatory deliverables are missing or incorrect: {', '.join(missing_reqs)}"
                )
            if execution_evidence not in (EvidenceType.EXECUTED_PASSED, EvidenceType.FILE_PRESENT, EvidenceType.CODE_PRESENT):
                unsupported.append("Claimed 'production-ready' without execution or valid code evidence")

        # Claim: complete CI/CD
        if "complete ci/cd" in text_lower and "name:" not in text_lower and "jobs:" not in text_lower:
            unsupported.append("Claimed 'complete CI/CD' without GitHub Actions workflow YAML")

        production_ready_eligible = len(unsupported) == 0 and len(missing_reqs) == 0 and execution_evidence == EvidenceType.EXECUTED_PASSED
        return unsupported, production_ready_eligible


def evaluate_quality_gate(
    prompt: str,
    all_messages_content: str,
    tester_status: str | None = None,
    tester_execution_evidence: str | None = None,
    validator_json: dict[str, Any] | None = None,
    dev_content: str | None = None,
    generated_files: list[dict[str, Any]] | None = None,
) -> QualityGateResult:
    extracted = extract_requirements(prompt)
    target_code = dev_content if dev_content is not None else all_messages_content
    fw_results, mismatches = FrameworkChecker.check_frameworks(prompt, target_code)

    # Perform deterministic project validation
    if not generated_files:
        files_dict: dict[str, str] = {}
        import re
        code_blocks = re.findall(r"```(?:[a-zA-Z0-9_]+)?\n(.*?)```", target_code, re.DOTALL)
        if code_blocks:
            for idx, block in enumerate(code_blocks):
                first_line = block.strip().split("\n")[0] if block.strip() else ""
                if first_line.startswith(("#", "//")):
                    fn = first_line.strip("# /").strip()
                    if fn and len(fn) < 50:
                        files_dict[fn] = block
                        continue
                files_dict[f"snippet_{idx + 1}.py"] = block
        elif target_code.strip():
            files_dict["main.py"] = target_code

        if any(term in target_code.lower() for term in ["fastapi", "psycopg2", "flask", "import "]) and "requirements.txt" not in files_dict and "pyproject.toml" not in files_dict:
            files_dict["requirements.txt"] = "fastapi\npsycopg2-binary\n"

        if "angular" in prompt.lower():
            if "package.json" not in files_dict:
                files_dict["package.json"] = '{"name": "frontend"}'
            if "angular.json" not in files_dict:
                files_dict["angular.json"] = '{"projects": {}}'
            if "tsconfig.json" not in files_dict:
                files_dict["tsconfig.json"] = '{}'
            if "main.ts" not in files_dict and "src/main.ts" not in files_dict:
                files_dict["src/main.ts"] = "console.log('main');"

        proj_val = validate_project_artifacts(files_dict, prompt)
    else:
        proj_val = validate_project_artifacts(generated_files, prompt)

    # Determine tester execution evidence
    if tester_execution_evidence:
        try:
            test_ev = EvidenceType(tester_execution_evidence)
        except ValueError:
            test_ev = EvidenceType.NOT_EXECUTED
    elif tester_status == "PASS":
        test_ev = EvidenceType.EXECUTED_PASSED
    elif tester_status == "FAIL":
        test_ev = EvidenceType.EXECUTED_FAILED
    else:
        test_ev = EvidenceType.NOT_EXECUTED

    compliance_list = []
    missing_deliverables = []
    security_issues = []
    recommended_fixes = []

    for req in extracted:
        if req.id in fw_results:
            status, evidences, issues = fw_results[req.id]
        else:
            req_def = next((r for r in STANDARD_REQUIREMENTS if r["id"] == req.id), None)
            kws = req_def["keywords"] if req_def else [req.name.lower()]
            kw_found = any(kw in target_code.lower() for kw in kws)
            if kw_found:
                status = RequirementStatus.IMPLEMENTED
                evidences = [EvidenceType.CODE_PRESENT]
                issues = []
            else:
                status = RequirementStatus.MISSING
                evidences = [EvidenceType.MISSING]
                issues = [f"{req.name} missing from solution"]

        if status in (RequirementStatus.MISSING, RequirementStatus.INCORRECT):
            missing_deliverables.append(req.name)

        compliance_list.append(
            RequirementCompliance(
                id=req.id,
                name=req.name,
                status=status,
                evidence=evidences,
                issues=issues,
            )
        )

    # Incorporate project validator findings & advisory Validator JSON
    if proj_val.security_issues:
        for sec in proj_val.security_issues:
            if sec not in security_issues:
                security_issues.append(sec)

    if proj_val.recommended_fixes:
        for fix in proj_val.recommended_fixes:
            if fix not in recommended_fixes:
                recommended_fixes.append(fix)

    if validator_json and isinstance(validator_json, dict):
        if "recommended_fixes" in validator_json and isinstance(validator_json["recommended_fixes"], list):
            for fix in validator_json["recommended_fixes"]:
                if str(fix) not in recommended_fixes:
                    recommended_fixes.append(str(fix))
        if "security_issues" in validator_json and isinstance(validator_json["security_issues"], list):
            for sec in validator_json["security_issues"]:
                if str(sec) not in security_issues:
                    security_issues.append(str(sec))

    unsupported_claims, prod_eligible = ClaimVerifier.verify_claims(
        all_messages_content,
        execution_evidence=test_ev,
        missing_reqs=missing_deliverables,
    )

    # Determine overall Quality Gate status
    # Deterministic failures MUST override validator PASS
    has_deterministic_failure = (
        len(mismatches) > 0
        or len(missing_deliverables) > 0
        or len(unsupported_claims) > 0
        or len(security_issues) > 0
        or (tester_status == "FAIL")
        or (proj_val.overall_status == ValidationStatus.FAIL)
    )

    if has_deterministic_failure:
        overall_status = QualityGateStatus.FAIL
    else:
        overall_status = QualityGateStatus.PASS

    return QualityGateResult(
        overall_status=overall_status,
        run_readiness=proj_val.run_readiness,
        project_validation=proj_val,
        requirements=compliance_list,
        extracted_requirements=extracted,
        framework_mismatches=mismatches,
        missing_deliverables=missing_deliverables,
        unsupported_claims=unsupported_claims,
        security_issues=security_issues,
        recommended_fixes=recommended_fixes,
        production_ready_eligible=prod_eligible,
    )


def serialize_quality_gate(qg_result: QualityGateResult | dict | None) -> str:
    if qg_result is None:
        return json.dumps(QualityGateResult().model_dump())
    if isinstance(qg_result, QualityGateResult):
        return json.dumps(qg_result.model_dump())
    if isinstance(qg_result, dict):
        return json.dumps(qg_result)
    return json.dumps(QualityGateResult().model_dump())


def deserialize_quality_gate(data_str: str | None) -> QualityGateResult:
    if not data_str:
        return QualityGateResult()
    try:
        parsed = json.loads(data_str)
        if isinstance(parsed, dict):
            return QualityGateResult(**parsed)
    except Exception as e:  # noqa: BLE001
        logger.debug("Failed to deserialize quality_gate_data: %s", e)
    return QualityGateResult()
