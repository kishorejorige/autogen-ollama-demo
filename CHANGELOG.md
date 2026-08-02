# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by **Keep a Changelog**, and this project follows **Semantic Versioning (SemVer)**.

## [0.9.0] - Unreleased

### Added

- **Workflow Export (JSON & ZIP)**: Endpoints `GET /api/workflows/{id}/export/json` and `GET /api/workflows/{id}/export/zip` to download full workflow state backup or zipped code artifacts (with auto-generated README.md if not present).
- **Sanitized ZIP Archives**: Path traversal protection, entry name sanitization, and duplicate file name handling.
- **Workflow Favorites**: Mark and unmark workflows as favorites (`POST /api/workflows/{id}/favorite` and `DELETE /api/workflows/{id}/favorite`) with ⭐ favorite toggle buttons on history cards and detail inspector.
- **Date-Range Filtering**: Optional query parameter `date_range` (`today`, `7d`, `30d`) on `GET /api/workflows` using UTC time boundaries, with strict 400 Bad Request validation for invalid range values.
- **Analytics & Stats Enhancements**: Extended `GET /api/workflows/stats` response and UI cards for Favorites count (`favorite_count`) and Average Iterations (`average_iterations`).
- **Frontend & Backend Test Suites**: Added test coverage for JSON/ZIP export, favorite toggles, date filtering, analytics cards, legacy SQLite schema migration, and export errors.

---

## [0.8.0] - Unreleased

### Added

- **Workflow Memory & Database Storage**: Persistent storage of complete and failed Loop Engineering workflows in SQLite using SQLAlchemy ORM (`app/database`).
- **History & Memory UI**: Angular History interface with paginated list, search bar by prompt, status filter dropdown, and summary statistics cards.
- **Workflow Detail Inspector**: In-depth workflow detail view with tabs for Overview Summary, Iterations Timeline (with collapsible feedback sections), Agent Messages Feed (ordered by sequence number), and Generated Files (with final artifacts listed first).
- **Run Again & Delete**: "Run Again" action populating previous prompts into the New Workflow tab without auto-starting execution, and confirmation modal for workflow deletion.
- **Docker Persistence**: Volume mount `./data:/app/data` in `docker-compose.yml` guaranteeing workflow database survival across container rebuilds.
- **FastAPI History Endpoints**: RESTful history API endpoints for listing workflows, retrieving workflow statistics, inspecting workflow details, and deleting workflows.

---

## [0.7.0] - Unreleased

### Added

- **Tester Agent**: Dedicated Senior QA agent inspecting code reviewer feedback and generated code, returning QA summaries, edge cases, test suggestions, and strict `PASS` or `FAIL` status.
- **Bounded Loop Engineering**: Bounded improvement loop sequence (Developer -> Reviewer -> Tester -> Decision) that retries code generation and repair based on reviewer/tester feedback up to 3 times, stopping with `NEEDS_ATTENTION` upon max retries.
- **Structured State Tracking**: Enriched SSE streaming workflow state tracking, containing workflow IDs, statuses, iteration history, and generated file maps.
- **Code Tab UI & Copy/Download**: Elegant Angular tabbed UI rendering the response feed and code artifacts panel side-by-side. Support selecting generated files, copy-to-clipboard with animation checkmarks, and browser-initiated file downloads.

---

## [0.6.0] - Unreleased

### Added

- Production-ready Docker support for FastAPI backend and Angular frontend.
- `docker-compose.yml` to launch backend and frontend services simultaneously.
- GitHub Actions CI workflows for backend linting and testing, frontend testing and building, and Docker image compilation validation.
- Health check configurations for backend (Python-based) and frontend (Wget-based) Docker images.
- Custom Nginx SPA configuration for routing in the frontend Angular production container.


---

## [0.1.0] - 2026-07-26

### Added

- Initial project structure
- Microsoft AutoGen integration
- Ollama integration
- Local Qwen model support
- First AI Assistant Agent
- Complete project documentation
- README
- MIT License
- CONTRIBUTING guide

### Documentation

- Project Overview
- Problem Statement
- Requirements
- Proof of Concept
- Estimation
- Wireframes
- Architecture
- Roadmap
- Risks
- Testing Strategy
- Deployment Guide
- Future Enhancements

### Repository

- GitHub repository initialized
- Professional project structure
- Clean Git history

