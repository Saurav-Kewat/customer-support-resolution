# Dockerfile for AI Customer Support Resolution System
# OpenEnv Environment - Multi-task support resolution training

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy project files first (before pip install)
COPY customer_support_env.py .
COPY Inference.py .
COPY server.py .
COPY requirements.txt .
COPY openenv.yaml .
COPY README.md .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --disable-pip-version-check \
    --compile -r requirements.txt

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Default environment variables
ENV API_BASE_URL=https://router.huggingface.co/v1
ENV MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
ENV CUSTOMER_SUPPORT_TASK=email_triage
ENV CUSTOMER_SUPPORT_SEED=42
ENV MAX_EPISODES=1
ENV PORT=7860

# Expose port for OpenEnv API server (HF Spaces uses 7860)
EXPOSE 7860

# Run OpenEnv API server (required for validation - exposes /reset, /step, /state endpoints)
CMD ["python", "server.py"]
