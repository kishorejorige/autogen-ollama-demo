import ast
import logging
import os
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RunReadiness(str, Enum):
    RUNNABLE = "RUNNABLE"
    PARTIALLY_RUNNABLE = "PARTIALLY_RUNNABLE"
    NOT_RUNNABLE = "NOT_RUNNABLE"
    UNKNOWN = "UNKNOWN"


class ValidationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class ProjectValidationResult(BaseModel):
    overall_status: ValidationStatus = ValidationStatus.FAIL
    run_readiness: RunReadiness = RunReadiness.NOT_RUNNABLE
    files_checked: list[str] = Field(default_factory=list)
    unresolved_imports: list[str] = Field(default_factory=list)
    undefined_symbols: list[str] = Field(default_factory=list)
    missing_model_attributes: list[str] = Field(default_factory=list)
    module_conflicts: list[str] = Field(default_factory=list)
    placeholder_files: list[str] = Field(default_factory=list)
    placeholder_reasons: list[str] = Field(default_factory=list)
    syntax_errors: list[str] = Field(default_factory=list)
    missing_dependency_files: list[str] = Field(default_factory=list)
    missing_required_files: list[str] = Field(default_factory=list)
    frontend_issues: list[str] = Field(default_factory=list)
    backend_issues: list[str] = Field(default_factory=list)
    database_issues: list[str] = Field(default_factory=list)
    docker_issues: list[str] = Field(default_factory=list)
    ci_issues: list[str] = Field(default_factory=list)
    test_issues: list[str] = Field(default_factory=list)
    documentation_issues: list[str] = Field(default_factory=list)
    security_issues: list[str] = Field(default_factory=list)
    recommended_fixes: list[str] = Field(default_factory=list)


# Standard library modules allowlist
PYTHON_STDLIB: set[str] = {
    "abc", "argparse", "array", "ast", "asyncio", "base64", "binascii", "bisect",
    "builtins", "calendar", "cmath", "collections", "concurrent", "configparser",
    "contextlib", "copy", "csv", "ctypes", "dataclasses", "datetime", "decimal",
    "difflib", "dis", "doctest", "email", "enum", "errno", "faulthandler", "fcntl",
    "filecmp", "fileinput", "fnmatch", "fractions", "functools", "gc", "getpass",
    "getopt", "gettext", "glob", "gzip", "hashlib", "heapq", "hmac", "html", "http",
    "imaplib", "importlib", "inspect", "io", "ipaddress", "itertools", "json",
    "keyword", "linecache", "locale", "logging", "math", "mimetypes", "multiprocessing",
    "operator", "os", "pathlib", "pickle", "pkgutil", "platform", "poplib", "posix",
    "pprint", "profile", "pstats", "py_compile", "queue", "random", "re", "resource",
    "rlcompleter", "sched", "select", "selectors", "shelve", "shutil", "signal",
    "site", "socket", "socketserver", "sqlite3", "ssl", "stat", "string", "struct",
    "subprocess", "sys", "sysconfig", "tarfile", "tempfile", "termios", "textwrap",
    "threading", "time", "timeit", "tkinter", "token", "tokenize", "traceback",
    "tracemalloc", "typing", "unicodedata", "unittest", "urllib", "uuid", "warnings",
    "weakref", "xml", "xmlrpc", "zipfile", "zipimport", "zlib"
}

# Popular third-party packages allowlist
THIRD_PARTY_ALLOWLIST: set[str] = {
    "fastapi", "sqlalchemy", "pydantic", "pytest", "jose", "jwt", "passlib",
    "uvicorn", "httpx", "starlette", "psycopg2", "asyncpg", "alembic", "jinja2",
    "requests", "urllib3", "dotenv", "docker", "autogen", "autogen_agentchat",
    "autogen_core", "autogen_ext", "flask", "anyio", "boto3", "celery", "redis",
    "cryptography", "click", "rich", "typer", "tqdm", "yaml", "setuptools", "wheel"
}

KNOWN_SHADOWED_PACKAGES: set[str] = {
    "fastapi", "sqlalchemy", "pydantic", "pytest", "jwt", "jose", "starlette", "angular"
}


# --- Modular Helper Functions ---

def validate_python_syntax(files: dict[str, str]) -> list[str]:
    """Parse all Python files using ast.parse and record any SyntaxErrors."""
    errors = []
    for filepath, content in files.items():
        if filepath.endswith(".py"):
            try:
                ast.parse(content, filename=filepath)
            except SyntaxError as e:
                line_no = e.lineno or 1
                msg = f"{filepath}: line {line_no}: {e.msg}"
                errors.append(msg)
    return errors


def extract_declared_python_modules(files: dict[str, str]) -> set[str]:
    """Extract set of Python module dot-paths from generated filenames."""
    declared = set()
    for filepath in files:
        cleaned = filepath.strip().replace("\\", "/")
        cleaned = cleaned.removeprefix("./")

        # Handle top-level or nested python files
        if cleaned.endswith(".py"):
            module_path = cleaned[:-3]
            parts = [p for p in module_path.split("/") if p]
            if parts:
                if parts[-1] == "__init__":
                    parts = parts[:-1]
                if parts:
                    declared.add(".".join(parts))
                    # Also register top-level name and basename
                    declared.add(parts[0])
                    declared.add(parts[-1])
    return declared


def parse_third_party_dependencies(files: dict[str, str]) -> set[str]:
    """Extract third-party package names from requirements.txt or pyproject.toml."""
    deps = set(THIRD_PARTY_ALLOWLIST)
    for filepath, content in files.items():
        fname = os.path.basename(filepath).lower()
        if fname == "requirements.txt":
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    pkg = re.split(r"[=<>]", line)[0].strip().lower().replace("-", "_")
                    if pkg:
                        deps.add(pkg)
        elif fname == "pyproject.toml":
            for line in content.splitlines():
                line = line.strip()
                match = re.search(r'^"?([a-zA-Z0-9_\-]+)"?\s*=', line)
                if match:
                    deps.add(match.group(1).lower().replace("-", "_"))
    return deps


def validate_local_imports(files: dict[str, str]) -> list[str]:
    """
    Parse AST imports across Python files and verify that non-stdlib/non-third-party
    imports map to valid generated modules.
    """
    declared_modules = extract_declared_python_modules(files)
    allowed_packages = parse_third_party_dependencies(files)
    unresolved = []

    for filepath, content in files.items():
        if not filepath.endswith(".py"):
            continue
        try:
            tree = ast.parse(content, filename=filepath)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod_name = alias.name.split(".")[0].lower()
                    if (
                        mod_name not in PYTHON_STDLIB
                        and mod_name not in allowed_packages
                        and mod_name not in declared_modules
                        and alias.name not in declared_modules
                    ):
                        err = f"Unresolved import '{alias.name}' in {filepath}"
                        if err not in unresolved:
                            unresolved.append(err)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    # Relative import is local
                    continue
                if node.module:
                    mod_name = node.module.split(".")[0].lower()
                    if mod_name not in PYTHON_STDLIB and mod_name not in allowed_packages:
                        full_mod = f"{node.module}"
                        if mod_name not in declared_modules and full_mod not in declared_modules:
                            err = f"Unresolved import 'from {node.module}' in {filepath}"
                            if err not in unresolved:
                                unresolved.append(err)

    return unresolved


def detect_undefined_symbols(files: dict[str, str]) -> tuple[list[str], list[str]]:
    """
    Detect calls to undefined/unimported functions and missing model attributes.
    """
    undefined_symbols = []
    missing_model_attrs = []

    # First pass: collect model classes and their defined fields/attributes across python files
    model_classes: dict[str, set[str]] = {}
    for filepath, content in files.items():
        if not filepath.endswith(".py"):
            continue
        try:
            tree = ast.parse(content, filename=filepath)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                cls_name = node.name
                if cls_name not in model_classes:
                    model_classes[cls_name] = set()
                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                        model_classes[cls_name].add(stmt.target.id)
                    elif isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                model_classes[cls_name].add(target.id)

    # Second pass: check for undefined calls and model attribute references
    for filepath, content in files.items():
        if not filepath.endswith(".py"):
            continue
        try:
            tree = ast.parse(content, filename=filepath)
        except SyntaxError:
            continue

        # Collect defined or imported names in this file
        defined_names: set[str] = set(dir(__builtins__))
        imported_names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined_names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_names.add(target.id)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imported_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imported_names.add(name)

        known_names = defined_names | imported_names

        # Check for specific undefined function calls in main app logic
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in ("get_user", "verify_password", "authenticate_user") and func_name not in known_names:
                    err = f"Call to undefined/unimported function '{func_name}' in {filepath}"
                    if err not in undefined_symbols:
                        undefined_symbols.append(err)

            # Check model attribute access like Todo.user_id
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                cls_name = node.value.id
                attr_name = node.attr
                if model_classes.get(cls_name) and attr_name == "user_id" and "user_id" not in model_classes[cls_name]:
                    err = f"Model '{cls_name}' does not have attribute '{attr_name}' referenced in {filepath}"
                    if err not in missing_model_attrs:
                        missing_model_attrs.append(err)

    return undefined_symbols, missing_model_attrs


def detect_module_shadowing(files: dict[str, str]) -> list[str]:
    """Detect top-level generated files or folders that shadow third-party packages."""
    conflicts = []
    for filepath in files:
        cleaned = filepath.strip().replace("\\", "/")
        parts = cleaned.split("/")

        # Flag top-level folders named after third-party packages (e.g. fastapi/, sqlalchemy/, pydantic/)
        if len(parts) > 1 and parts[0] in THIRD_PARTY_ALLOWLIST and parts[0] != "backend":
            top_level = parts[0]
            conflicts.append(f"Top-level folder '{parts[0]}/' shadows the third-party '{top_level}' package")
    return conflicts


def detect_placeholder_files(files: dict[str, str]) -> tuple[list[str], list[str]]:
    """Detect mandatory files containing only placeholders, comments, or empty bodies."""
    placeholders = []
    reasons = []

    for filepath, content in files.items():
        fname = os.path.basename(filepath).lower()
        content_strip = content.strip()

        # Check README.md
        if fname in ("readme.md", "readme") and (len(content_strip) < 100 or "Add installation instructions" in content or "# Documentation\n# Add" in content):
            placeholders.append(filepath)
            reasons.append(f"README file '{filepath}' contains only placeholder text")
            continue

        # Check solution.py or main source files
        if fname == "solution.py" and (len(content_strip) < 100 or "Add API references" in content):
            placeholders.append(filepath)
            reasons.append(f"Source file '{filepath}' is a placeholder file")
            continue

        # Check for hardcoded secret key placeholder
        if ("your-secret-key" in content.lower() or "your_secret_key" in content.lower()) and filepath not in placeholders:
            placeholders.append(filepath)
            reasons.append(f"Hardcoded placeholder secret key in '{filepath}'")
            continue

        # Check for placeholder API URL
        if ("your-api-url" in content.lower() or "your_api_url" in content.lower()) and filepath not in placeholders:
            placeholders.append(filepath)
            reasons.append(f"Placeholder API URL 'your-api-url' found in '{filepath}'")

    return placeholders, reasons


def validate_dependencies(prompt: str, files: dict[str, str]) -> tuple[list[str], list[str]]:
    """Verify required dependency and configuration files exist for the requested stack."""
    prompt_lower = prompt.lower()
    missing_deps = []
    missing_req_files = []

    filenames_lower = {os.path.basename(f).lower(): f for f in files}

    # Python backend checks
    if any(term in prompt_lower for term in ["fastapi", "python", "backend"]):
        has_python_dep = any(f in filenames_lower for f in ["requirements.txt", "pyproject.toml", "pipfile", "uv.lock"])
        if not has_python_dep:
            missing_deps.append("requirements.txt or pyproject.toml")

    # Angular frontend checks
    if "angular" in prompt_lower:
        required_angular = ["package.json", "angular.json", "tsconfig.json", "main.ts"]
        for req_f in required_angular:
            if not any(req_f in f.lower() for f in files):
                missing_deps.append(req_f)
                missing_req_files.append(req_f)

    # Docker checks
    if "docker" in prompt_lower:
        has_docker = any("dockerfile" in f.lower() or "docker-compose" in f.lower() or "compose.yaml" in f.lower() for f in files)
        if not has_docker:
            missing_deps.append("Dockerfile or docker-compose.yml")

    # GitHub Actions checks
    if any(term in prompt_lower for term in ["github actions", "ci/cd", "ci"]):
        has_ci = any(".github/workflows/" in f.replace("\\", "/") for f in files)
        if not has_ci:
            missing_deps.append(".github/workflows/ci.yml")

    return missing_deps, missing_req_files


def validate_fastapi(prompt: str, files: dict[str, str]) -> tuple[list[str], list[str]]:
    """FastAPI specific checks."""
    issues = []
    security = []
    if "fastapi" not in prompt.lower():
        return issues, security

    has_fastapi_import = False

    for filepath, content in files.items():
        if filepath.endswith(".py"):
            if "from fastapi import" in content or "import fastapi" in content:
                has_fastapi_import = True
            if "app.test_client()" in content:
                issues.append(f"FastAPI test file '{filepath}' uses Flask-style app.test_client() instead of FastAPI TestClient")
            if "your-secret-key" in content.lower() or 'secret_key = "your-secret-key"' in content.lower():
                security.append(f"Hardcoded placeholder JWT secret key 'your-secret-key' found in '{filepath}'")

    if not has_fastapi_import:
        issues.append("FastAPI application code is missing 'from fastapi import ...'")

    return issues, security


def validate_angular(prompt: str, files: dict[str, str]) -> list[str]:
    """Angular specific checks including template-component method mismatches."""
    issues = []
    if "angular" not in prompt.lower():
        return issues

    ts_methods: set[str] = set()
    template_methods: list[tuple[str, str]] = []  # (method_name, filepath)

    for filepath, content in files.items():
        if filepath.endswith(".ts"):
            # Extract method names from TypeScript class
            matches = re.findall(r"(?:async\s+)?([a-zA-Z0-9_]+)\s*\([^)]*\)\s*(?::|\{)", content)
            for m in matches:
                if m not in ("constructor", "if", "for", "while", "switch", "catch"):
                    ts_methods.add(m)
        elif filepath.endswith(".html"):
            # Extract method bindings like (click)="deleteTodo(todo.id)"
            matches = re.findall(r"\((?:click|submit|change|ngSubmit)\)=\"([a-zA-Z0-9_]+)\(", content)
            for m in matches:
                template_methods.append((m, filepath))

    for method_name, filepath in template_methods:
        if method_name not in ts_methods:
            issues.append(f"Angular template '{filepath}' references method '{method_name}' which is missing from TypeScript component")

    return issues


def validate_postgresql(prompt: str, files: dict[str, str]) -> tuple[list[str], list[str]]:
    """PostgreSQL specific checks."""
    issues = []
    mismatches = []
    if "postgresql" not in prompt.lower() and "postgres" not in prompt.lower():
        return issues, mismatches

    has_pg_driver = False
    for content in files.values():
        if "psycopg2" in content or "asyncpg" in content or "postgresql://" in content:
            has_pg_driver = True
            break

    if not has_pg_driver:
        issues.append("PostgreSQL requested but no driver (psycopg2/asyncpg) or database URL configured")

    return issues, mismatches


def validate_project_artifacts(
    generated_files: list[dict[str, Any]] | dict[str, str],
    prompt: str = "",
) -> ProjectValidationResult:
    """Main entry point for deterministic project artifact validation."""
    files_map: dict[str, str] = {}
    if isinstance(generated_files, list):
        for gf in generated_files:
            fname = gf.get("filename", "")
            content = gf.get("content", "")
            if fname:
                files_map[fname] = content
    elif isinstance(generated_files, dict):
        files_map = generated_files

    files_checked = list(files_map.keys())

    # Run modular validations
    syntax_errors = validate_python_syntax(files_map)
    unresolved_imports = validate_local_imports(files_map)
    undefined_symbols, missing_model_attrs = detect_undefined_symbols(files_map)
    module_conflicts = detect_module_shadowing(files_map)
    placeholder_files, placeholder_reasons = detect_placeholder_files(files_map)
    missing_deps, missing_req_files = validate_dependencies(prompt, files_map)
    fastapi_issues, fastapi_security = validate_fastapi(prompt, files_map)
    angular_issues = validate_angular(prompt, files_map)
    pg_issues, pg_mismatches = validate_postgresql(prompt, files_map)

    # Aggregate issues
    backend_issues = fastapi_issues
    frontend_issues = angular_issues
    database_issues = pg_issues
    security_issues = list(dict.fromkeys(fastapi_security + [r for r in placeholder_reasons if "secret key" in r.lower()]))

    recommended_fixes = []
    if syntax_errors:
        recommended_fixes.append("Fix Python syntax errors in generated files")
    if unresolved_imports:
        recommended_fixes.append("Ensure all referenced local modules (e.g. models.py, database.py) are generated and imported")
    if undefined_symbols:
        recommended_fixes.append("Define or import missing functions (e.g. get_user, verify_password)")
    if module_conflicts:
        recommended_fixes.append("Remove top-level folders/files that shadow third-party packages (e.g. top-level fastapi/)")
    if placeholder_files:
        recommended_fixes.append("Replace placeholder content in README.md and source files with full implementation")
    if missing_deps:
        recommended_fixes.append("Include all required build and dependency configuration files (e.g. requirements.txt, package.json)")

    # Compute overall status
    has_failures = bool(
        syntax_errors or unresolved_imports or undefined_symbols or missing_model_attrs
        or module_conflicts or placeholder_files or missing_deps or missing_req_files
        or backend_issues or frontend_issues or database_issues or security_issues or pg_mismatches
    )

    overall_status = ValidationStatus.FAIL if has_failures else ValidationStatus.PASS

    # Compute Run Readiness
    if syntax_errors or unresolved_imports or undefined_symbols or module_conflicts or missing_req_files or ("requirements.txt or pyproject.toml" in missing_deps and "fastapi" in prompt.lower()):
        run_readiness = RunReadiness.NOT_RUNNABLE
    elif database_issues or frontend_issues or placeholder_files:
        run_readiness = RunReadiness.PARTIALLY_RUNNABLE
    elif overall_status == ValidationStatus.PASS:
        run_readiness = RunReadiness.RUNNABLE
    else:
        run_readiness = RunReadiness.NOT_RUNNABLE

    return ProjectValidationResult(
        overall_status=overall_status,
        run_readiness=run_readiness,
        files_checked=files_checked,
        unresolved_imports=unresolved_imports,
        undefined_symbols=undefined_symbols,
        missing_model_attributes=missing_model_attrs,
        module_conflicts=module_conflicts,
        placeholder_files=placeholder_files,
        placeholder_reasons=placeholder_reasons,
        syntax_errors=syntax_errors,
        missing_dependency_files=missing_deps,
        missing_required_files=missing_req_files,
        frontend_issues=frontend_issues,
        backend_issues=backend_issues,
        database_issues=database_issues,
        docker_issues=[],
        ci_issues=[],
        test_issues=[],
        documentation_issues=[],
        security_issues=security_issues,
        recommended_fixes=recommended_fixes,
    )
