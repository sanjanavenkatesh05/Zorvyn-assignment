# =============================================================================
# Zorvyn Finance Backend — Dockerfile
# =============================================================================
# Builds a lightweight Python 3.11 image for the FastAPI application.
#
# Build:   docker build -t zorvyn-finance-api .
# Run:     docker run -p 8000:8000 zorvyn-finance-api
#
# In practice, use docker-compose.yml which handles networking and MongoDB.
# =============================================================================

# ── Base Image ───────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── Environment Variables ────────────────────────────────────────────────────
# Prevent Python from writing .pyc files and enable unbuffered output
# so that logs appear immediately in Docker logs.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ── Working Directory ───────────────────────────────────────────────────────
WORKDIR /app

# ── Install Dependencies ────────────────────────────────────────────────────
# Copy requirements first to leverage Docker layer caching.
# Dependencies only re-install when requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy Application Source ─────────────────────────────────────────────────
COPY . .

# ── Expose Port ─────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Run the Application ─────────────────────────────────────────────────────
# --reload enables hot-reloading during development (via volume mount).
# In production, remove --reload and add --workers N.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
