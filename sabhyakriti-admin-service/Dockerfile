FROM python:3.11-slim AS base

# Security: run as non-root
RUN groupadd --system appgroup && useradd --system --gid appgroup appuser

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY application/ ./application/
COPY presentation/ ./presentation/
COPY main.py .

# Ensure non-root ownership
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8007

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8007

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007", "--workers", "2"]
