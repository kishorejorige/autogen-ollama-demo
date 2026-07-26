# AutoGen + Ollama Demo

A local-first AI agent project built with Microsoft AutoGen and Ollama.

This project demonstrates how to run AI agents locally using open-source language models without relying on paid cloud APIs.

## Features

- Microsoft AutoGen integration
- Local Ollama model support
- Works with Windows and WSL Ubuntu
- Uses `uv` for Python dependency management
- Local-first and privacy-friendly
- Ready for multi-agent expansion
- Complete project documentation

## Current Status

| Feature | Status |
|---|---|
| Project setup | ✅ Complete |
| Ollama connection | ✅ Complete |
| First AutoGen agent | ✅ Complete |
| Documentation | ✅ Complete |
| Multi-agent workflow | 🚧 Planned |
| Automated tests | 🚧 Planned |
| Docker support | 🚧 Planned |

## Architecture

```text
User
  |
  v
AutoGen Assistant Agent
  |
  v
Ollama Client
  |
  v
Windows Ollama Server
  |
  v
Local Qwen Model

Technology Stack:

Python 3.12+
Microsoft AutoGen
Ollama
Qwen3
uv
Git and GitHub
Windows 11
WSL Ubuntu

Prerequisites

Before running the project, install:

Python 3.12 or later
uv
Git
Ollama on Windows
A supported Ollama model

Recommended models:

qwen3:1.7b
qwen2.5-coder:1.5b
nomic-embed-text

Installation

Clone the repository:

git clone https://github.com/kishorejorige/autogen-ollama-demo.git
cd autogen-ollama-demo

Install dependencies:

uv sync

Ollama Configuration

Make sure Ollama is running on Windows.

Verify access from WSL:

curl http://host.docker.internal:11434/api/tags

Create a .env file:

OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:1.7b

Run the Application

uv run python main.py

Example prompt:

Explain what an AI agent is in two simple sentences.

Project Structure:

autogen-demo/
├── agents/
├── app/
├── config/
├── data/
├── docs/
├── logs/
├── scripts/
├── tests/
├── main.py
├── pyproject.toml
├── README.md
└── uv.lock

Documentation

The docs/ directory includes:

Project overview
Problem statement
Requirements
Proof of concept
Estimation
Wireframes
Architecture
Roadmap
Risks
Testing strategy
Deployment guide
Future enhancements

Roadmap

Version 0.1.0

Local Ollama integration
First AutoGen assistant
Complete documentation
Basic project structure

Version 0.2.0

Manager Agent
Python Developer Agent
Multi-agent collaboration
Improved configuration

Future Versions

Conversation memory
Web interface
RAG integration
Docker deployment
CI/CD
Cloud deployment

Author
Kishore Kumar

Python Developer focused on AI agents, automation, FastAPI, local LLMs, and practical open-source projects.

License

This project will use the MIT License.

