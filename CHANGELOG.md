# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by **Keep a Changelog**, and this project follows **Semantic Versioning (SemVer)**.

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

