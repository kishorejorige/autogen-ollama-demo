# Proof of Concept (POC)

## Document Information

| Field | Value |
|-------|-------|
| Document | Proof of Concept |
| Project | AutoGen + Ollama Demo |
| Version | v0.1.0 |
| Status | Completed |
| Author | Kishore Kumar |
| Last Updated | 2026-07-24 |

---

# Purpose

The purpose of this Proof of Concept (POC) is to verify that Microsoft AutoGen can successfully communicate with a locally hosted Ollama model.

---

# Objective

Demonstrate a working AI agent running locally without using paid cloud APIs.

---

# Components

## AI Framework

- Microsoft AutoGen

## Model Provider

- Ollama

## Language Model

- qwen3:1.7b

---

# Workflow

```text
User
 │
 ▼
Assistant Agent
 │
 ▼
Ollama Client
 │
 ▼
Windows Ollama Server
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

# Test Performed

The following prompt was executed:

> Explain what an AI agent is in two simple sentences.

The Assistant Agent successfully generated a response using the local Ollama model.

---

# Success Criteria

- AutoGen installed successfully.
- Ollama connection established.
- Local model loaded.
- AI agent responded correctly.
- No cloud APIs used.

---

# Result

**Status:** ✅ Successful

The project successfully demonstrated that Microsoft AutoGen can communicate with Ollama and execute AI tasks entirely on a local machine.