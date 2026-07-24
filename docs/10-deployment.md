# Deployment

## Document Information

| Field | Value |
|-------|-------|
| Document | Deployment |
| Project | AutoGen + Ollama Demo |
| Version | v0.1.0 |
| Status | Draft |
| Author | Kishore Kumar |
| Last Updated | 2026-07-24 |

---

# Purpose

This document explains how to deploy and run the AutoGen + Ollama Demo project in different environments. The initial focus is local development, with future support for containerized and cloud deployments.

---

# Deployment Environments

| Environment | Status |
|------------|--------|
| Local Development | ✅ Supported |
| WSL Ubuntu | ✅ Supported |
| Docker | 🚧 Planned |
| VPS | ⏳ Future |
| Cloud | ⏳ Future |

---

# Local Deployment

## Prerequisites

- Windows 11
- WSL Ubuntu
- Python 3.12+
- Git
- uv
- Ollama installed on Windows

---

## Clone Repository

```bash
git clone https://github.com/kishorejorige/autogen-ollama-demo.git
cd autogen-ollama-demo
```

---

## Install Dependencies

```bash
uv sync
```

---

## Configure Environment

Create a `.env` file:

```text
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:1.7b
```

---

## Verify Ollama

```bash
curl http://host.docker.internal:11434/api/tags
```

---

## Run the Application

```bash
uv run python main.py
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
├── main.py
├── .env
├── pyproject.toml
└── uv.lock
```

---

# Docker Deployment (Planned)

Future Docker deployment will include:

- Dockerfile
- docker-compose.yml
- Persistent configuration
- Volume mounting
- Environment variables

---

# Future Cloud Deployment

Possible deployment targets:

- Oracle Cloud Free Tier
- DigitalOcean
- Hetzner
- Hostinger VPS
- Azure Virtual Machine

---

# Deployment Checklist

- Repository cloned
- Dependencies installed
- Environment configured
- Ollama running
- AI model available
- Application starts successfully
- AI agent responds correctly

---

# Troubleshooting

| Problem | Solution |
|----------|----------|
| Ollama not reachable | Verify Ollama is running on Windows |
| Connection refused | Check `OLLAMA_BASE_URL` |
| Model not found | Run `ollama list` on Windows |
| Missing dependencies | Run `uv sync` |
| Application fails to start | Review logs and configuration |

---

# Conclusion

The project is designed for simple local deployment while remaining flexible enough to support Docker containers and cloud environments in future releases.
