# AutoGen + Ollama Demo

A **local-first Multi-Agent AI system** built with **Microsoft AutoGen** and **Ollama**.

This project demonstrates how to build and orchestrate multiple AI agents locally using open-source language models without relying on paid cloud APIs.

---
![Release](https://img.shields.io/github/v/release/kishorejorige/autogen-ollama-demo)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Angular](https://img.shields.io/badge/Angular-20-red)
![License](https://img.shields.io/github/license/kishorejorige/autogen-ollama-demo)

# Features

- 🤖 Microsoft AutoGen 0.7.5
- 📋 Manager Agent (specialist delegation)
- 💻 Python Developer Agent (writes code)
- 🔍 Code Reviewer Agent (provides design & style feedback)
- 🧪 Tester Agent (identifies defects & suggests test cases)
- 📝 Documentation Agent (writes manuals and usage guides)
- 🛡️ Evidence-Based Quality Gates (deterministic verification overriding optimistic agent claims)
- 🚀 Deterministic Run-Readiness Validator (AST import, syntax, symbol, shadowing, placeholder & stack dependency checks)
- 🔄 Bounded Loop Engineering workflow (max 3 retry-repair cycles)
- 💾 Workflow Memory & SQLite Persistence (`app/database`)
- 📦 Structured ZIP Export (`quality-report.json`, `iterations/` history, and verified `final/` deliverables)
- ⚡ Real-Time SSE Defect Events (streamed project validation feedback)
- ⭐ Favorites System (toggle favorites & analytics tracking)
- 📅 Date-Range Filtering (Today, Last 7 Days, Last 30 Days in UTC)
- 📜 History & Memory UI Interface with search, status filtering, and statistics cards
- 🔍 Workflow Detail Inspector & Quality Matrix (Overview, Iterations Timeline, Messages Feed, Artifacts, Run Readiness)
- ⚡ Run Again action (loads prompt into New Workflow tab without auto-executing)
- 🦙 Ollama Integration (local AI models execution)
- ⚙️ Environment-based Configuration
- 📦 Tabbed UI Panel (Response Feed & Generated Artifacts side-by-side)
- 📋 Code Editor Viewer with line numbering, Copy-to-Clipboard & File Downloads

---

# Current Status

| Feature | Status |
|----------|--------|
| Project Setup | ✅ Complete |
| Ollama Integration | ✅ Complete |
| Modular Architecture | ✅ Complete |
| Manager Agent | ✅ Complete |
| Python Developer Agent | ✅ Complete |
| Reviewer Agent | ✅ Complete |
| Tester Agent | ✅ Complete |
| Documentation Agent | ✅ Complete |
| Bounded Loop Engineering | ✅ Complete |
| Evidence-Based Quality Gates | ✅ Complete |
| Deterministic Project Run-Readiness | ✅ Complete |
| Code Copy / Download UI | ✅ Complete |
| Workflow Memory & Database Persistence | ✅ Complete |
| Frontend History Interface | ✅ Complete |
| Workflow Export (JSON & Structured ZIP) | ✅ Complete |
| Favorite Toggles & Analytics | ✅ Complete |
| Date-Range Filtering | ✅ Complete |
| Automated Tests (Pytest & Karma) | ✅ Complete |
| GitHub Actions CI | ✅ Complete |
| Docker Support & Volume Persistence | ✅ Complete |

---

# Architecture

```text
                       User
                         │
                         ▼
                   Manager Agent
                         │
                         ▼
             ┌──► Python Developer ◄──┐
             │           │            │
             │           ▼            │
             │     Code Reviewer      │ (Fail Loop, max 3)
             │           │            │
             │           ▼            │
             │      Tester Agent ─────┘
             │           │
             │           ▼ (Pass)
             │  Documentation Agent
             │           │
             └───────────┼────────────
                         ▼
                     Solution
```

---

# Technology Stack

- Python 3.12+
- Microsoft AutoGen 0.7.5
- Ollama
- Qwen3
- uv
- Git
- GitHub
- Windows 11
- WSL Ubuntu

---

# Prerequisites

Install the following software before running the project:

- Python 3.12+
- uv
- Git
- Ollama
- Windows 11 (or Linux)
- WSL Ubuntu (Recommended for Windows)

---

# Recommended Ollama Models

```text
qwen3:1.7b
qwen2.5-coder:1.5b
nomic-embed-text
```

---

# Installation

## Clone the Repository

```bash
git clone https://github.com/kishorejorige/autogen-ollama-demo.git
cd autogen-ollama-demo
```

## Install Dependencies

```bash
uv sync
```

---

# Ollama Configuration

Verify Ollama is running:

```bash
curl http://host.docker.internal:11434/api/tags
```

Create a `.env` file:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:1.7b
```

---

# Usage

## Interactive Mode

```bash
uv run python main.py
```

Example:

```text
Enter your task:
Create a Python function that calculates factorial
```

---

## Command Line Mode

```bash
uv run python main.py "Create a Python REST API"
```

Example:

```bash
uv run python main.py "Create a Python function that reverses a string"
```

---

## Web Interface (Native Development Mode)

To run the web interface natively, start both the FastAPI backend and the Angular frontend:

### 1. Start the FastAPI Backend
```bash
uv run uvicorn app.api:app --host 0.0.0.0 --port 8888
```

### 2. Start the Angular Frontend
Navigate to the `frontend` directory, install dependencies, and start the development server:
```bash
cd frontend
npm install
npm run start
```
Once both servers are running, open your browser and navigate to [http://localhost:4201](http://localhost:4201).

---

## Docker Compose Mode (Production Ready)

You can run the entire stack (FastAPI backend and Angular frontend) containerized using Docker Compose.

### Quick Start

1. **Required Ollama Setup**:
   Ensure Ollama is running on your Windows host. You can check if Ollama is listening by running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Docker Network / host.docker.internal Setup**:
   - On Windows/macOS, Docker containers access the host automatically using `http://host.docker.internal:11434`.
   - On Linux, if Docker doesn't map the gateway automatically, the `docker-compose.yml` configures `extra_hosts` to bind `host.docker.internal` to the host gateway.
   - Ensure Ollama allows connection from WSL/containers. Set the environment variable `OLLAMA_HOST=0.0.0.0` on your Windows host before starting Ollama.

3. **Start the containers**:
   ```bash
   docker compose up -d
   ```

4. **Verify Service URLs & Health Checks**:
   - **Frontend Dashboard:** [http://localhost:4201](http://localhost:4201) (served via Nginx)
   - **Backend API Gateway:** [http://localhost:8888](http://localhost:8888) (served via FastAPI)
   - **Backend Health Check:** `curl http://localhost:8888/health` (should return `{"status":"healthy"}`)
   - **Frontend Health Check:** `curl -I http://localhost:4201` (should return `200 OK`)

5. **Stop and Rebuild Containers**:
   - **Rebuild and restart:**
     ```bash
     docker compose up -d --build
     ```
   - **Stop containers:**
     ```bash
     docker compose down
     ```


---

# Workflow Memory & History

AutoGen Orchestrator automatically records every completed, failed, or interrupted Loop Engineering workflow in an embedded SQLite database.

## Database Configuration

- **Default Location**: `./data/autogen_demo.db`
- **Environment Variable**: `DATABASE_URL` (e.g. `sqlite:///./data/autogen_demo.db` or PostgreSQL connection string).
- **SQLite Pragmas**: `check_same_thread=False` and `PRAGMA foreign_keys=ON` are enforced automatically.

## History API Endpoints

- `GET /api/workflows`: List workflows with pagination (`limit`, `offset`), case-insensitive `search` on prompts, and `status` filtering (`COMPLETE`, `NEEDS_ATTENTION`, `FAILED`, `RUNNING`).
- `GET /api/workflows/stats`: Get summary metrics (total, completed, failed, needs attention, running workflows, and average iterations).
- `GET /api/workflows/{workflow_id}`: Retrieve full detail of a workflow including sorted iterations, ordered agent messages, and generated files with final artifacts listed first.
- `DELETE /api/workflows/{workflow_id}`: Delete a workflow and cascade delete all associated iterations, messages, and files.

## Docker Data Persistence

`docker-compose.yml` mounts `./data:/app/data` into the backend container so SQLite database records survive container restarts and rebuilds.

> Note: Running `docker compose down -v` with named volumes removes volume data. The host bind mount `./data:/app/data` preserves your SQLite database file.

## "Run Again" Behavior

Clicking "Run Again" on any workflow card or detail view copies the original prompt into the **New Workflow** input box and switches to the input view without automatically executing the task.

## Clearing Local History

You can clear workflow history by:
1. Using the **Delete Workflow** button inside any workflow detail view in the web UI.
2. Stopping the server and removing the SQLite database file:
   ```bash
   rm data/autogen_demo.db*
   ```

## Current Limitations

- History queries run directly against the local SQLite database. High-throughput concurrency environments should configure PostgreSQL via `DATABASE_URL`.
- Workflows running concurrently share short-lived database transactions.

---

# Example Workflow

```text
User
 │
 ▼
Create a Python function that calculates factorial

Manager Agent
 │
 ▼
Analyzes the task
Chooses the correct specialist

Python Developer Agent
 │
 ▼
Generates clean Python code

Final Response
```

---

# Project Structure

```text
autogen-demo/
│
├── agents/
│   ├── assistant.py
│   ├── manager.py
│   └── developer.py
│
├── app/
│
├── config/
│
├── data/
│
├── docs/
│
├── logs/
│
├── scripts/
│
├── tests/
│
├── main.py
├── pyproject.toml
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
└── uv.lock
```

---

# Documentation

The `docs/` directory contains:

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

---

# Roadmap

## Version 0.1.0 ✅

- Local Ollama Integration
- First AutoGen Assistant
- Professional Documentation
- Project Structure
- MIT License
- Contributing Guide
- Changelog

---

## Version 0.2.0 🚧

- Manager Agent
- Python Developer Agent
- RoundRobinGroupChat
- Dynamic Task Input
- Improved Configuration
- Production Readiness
- GitHub Actions
- Automated Tests

---

## Future Versions

- Research Agent
- Documentation Agent
- Code Reviewer Agent
- Conversation Logging
- Conversation Memory
- RAG Integration
- Web Interface
- Docker Deployment
- CI/CD Pipeline
- Cloud Deployment

---

# Project Evolution

```text
v0.1.0
│
├── Single Assistant
├── Ollama Integration
├── Documentation
└── Modular Foundation

Phase 2
│
├── Manager Agent
├── Python Developer Agent
├── RoundRobinGroupChat
├── Dynamic Task Input
└── Multi-Agent Foundation

Future
│
├── Research Agent
├── Documentation Agent
├── Reviewer Agent
├── Multi-Agent Collaboration
├── Conversation Memory
└── AI Engineering Platform
```

---

# Contributing

Contributions, ideas, and suggestions are welcome.

Please read the **CONTRIBUTING.md** guide before submitting pull requests.

---

# License

This project is licensed under the **MIT License**.

See the **LICENSE** file for details.

---

# Author

**Kishore Kumar**

Python Developer focused on:

- AI Agents
- Python Automation
- FastAPI
- Local LLMs
- AI Engineering
- Open Source Projects

GitHub:
https://github.com/kishorejorige

---

# Acknowledgements

- Microsoft AutoGen
- Ollama
- Qwen Models
- Python Community
- Open Source Community
