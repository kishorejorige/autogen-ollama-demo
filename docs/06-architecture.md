# Architecture

## Document Information

| Field | Value |
|-------|-------|
| Document | Architecture |
| Project | AutoGen + Ollama Demo |
| Version | v0.1.0 |
| Status | Draft |
| Author | Kishore Kumar |
| Last Updated | 2026-07-24 |

---

# Purpose

This document describes the overall architecture of the AutoGen + Ollama Demo project, including its components, data flow, and design principles.

---

# Design Principles

- Local-first
- Modular architecture
- Reusable components
- Simple configuration
- Testable code
- Open-source friendly

---

# High-Level Architecture

```text
                 User
                   │
                   ▼
          AutoGen Application
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
   Assistant Agent     Future Agents
         │                   │
         └─────────┬─────────┘
                   ▼
      Ollama Chat Client
                   │
                   ▼
      Windows Ollama Server
                   │
                   ▼
          Qwen3 / Local LLM
```

---

# Project Structure

```text
autogen-demo/
├── agents/
├── app/
├── config/
├── data/
├── docs/
├── logs/
├── scripts/
├── tests/
├── .env.example
├── pyproject.toml
├── README.md
└── uv.lock
```

---

# Component Description

## User

Starts conversations with the AI agent.

## AutoGen Application

Coordinates all application logic and AI interactions.

## Assistant Agent

Receives prompts and generates responses using the configured language model.

## Ollama Client

Connects AutoGen to the local Ollama server.

## Ollama Server

Hosts local language models.

## Local Model

Processes prompts and generates responses.

---

# Data Flow

```text
User
 │
 ▼
Prompt
 │
 ▼
Assistant Agent
 │
 ▼
Ollama Client
 │
 ▼
Qwen3 Model
 │
 ▼
Generated Response
 │
 ▼
User
```

---

# Configuration

Configuration values are stored in `.env`.

Example:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:1.7b
```

---

# Future Architecture

Future versions may include:

- Manager Agent
- Research Agent
- Python Developer Agent
- Code Reviewer Agent
- Memory Module
- Vector Database
- Web UI
- Docker Deployment

---

# Architecture Goals

- Easy to understand
- Easy to extend
- Easy to maintain
- Local execution
- Minimal dependencies
- Production-ready structure

