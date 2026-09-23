# --- Multi-Stage Production Build ---
# [Interview Design Note]: Using a multi-stage deterministic build ensures the final image
# is as small and secure as possible by dropping raw source files and compilers.

# Stage 1: Dependency Builder
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
# Compile wheels (faster subsequent installs, ignores OS C-extensions)
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final Runtime Image
FROM python:3.11-slim
WORKDIR /app

# Copy pure wheels from builder stage
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache /wheels/*

COPY . .

# [Interview Design Note]: Security Best Practice - Do not run containers as root
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Bind on all interfaces specifically overriding localhost binding
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
