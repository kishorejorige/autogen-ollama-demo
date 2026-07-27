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
- 👨‍💼 Manager Agent
- 👨‍💻 Python Developer Agent
- 🔄 RoundRobinGroupChat Team Workflow
- 🦙 Ollama Integration
- ⚡ Dynamic Task Input (CLI & Interactive)
- ⚙️ Environment-based Configuration
- 📚 Modular Project Structure
- 📝 Professional Documentation
- 🌐 Local-First AI Development
- 🔀 Git Feature Branch Workflow

---

# Current Status

| Feature | Status |
|----------|--------|
| Project Setup | ✅ Complete |
| Ollama Integration | ✅ Complete |
| Modular Architecture | ✅ Complete |
| Manager Agent | ✅ Complete |
| Python Developer Agent | ✅ Complete |
| RoundRobinGroupChat | ✅ Complete |
| Dynamic Task Input | ✅ Complete |
| Documentation | ✅ Complete |
| Automated Tests | 🚧 Planned |
| GitHub Actions CI | 🚧 Planned |
| Research Agent | 🚧 Planned |
| Documentation Agent | 🚧 Planned |
| Reviewer Agent | 🚧 Planned |
| Docker Support | 🚧 Planned |

---

# Architecture

```text
                    User
                      │
                      ▼
           RoundRobinGroupChat
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
  Manager Agent          Python Developer Agent
         │                         │
         └────────────┬────────────┘
                      ▼
                Final Response
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

## Web Interface Mode

To run the web interface, start both the FastAPI backend and the Angular frontend:

### 1. Start the FastAPI Backend
```bash
uv run uvicorn app.api:app --host 0.0.0.0 --port 8000
```

### 2. Start the Angular Frontend
Navigate to the `frontend` directory, install dependencies, and start the development server:
```bash
cd frontend
npm install
npm run start
```
Once both servers are running, open your browser and navigate to [http://localhost:4200](http://localhost:4200).

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
