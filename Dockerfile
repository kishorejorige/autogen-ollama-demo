FROM python:3.12-slim-bookworm

# Copy uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Configure python and uv environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy backend application files
COPY app/ ./app
COPY config/ ./config
COPY agents/ ./agents
COPY main.py ./

# Create data directory, non-root user, and set permissions
RUN mkdir -p /app/data && \
    useradd -u 10001 -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose FastAPI backend port
EXPOSE 8888

# Health check using python's built-in urllib
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8888/health')"

# Run uvicorn server in production mode
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8888"]
