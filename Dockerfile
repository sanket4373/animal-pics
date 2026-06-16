
# Stage 1: Builder - Install dependencies
FROM python:3.11-slim AS builder

WORKDIR /builder

# Configure Poetry to create virtualenv in project directory
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1

RUN pip install poetry pytest-cov

# Install dependencies only (not the app itself yet)
# This layer is cached unless pyproject.toml/poetry.lock changes
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root


# Stage 2: Runtime - Minimal production image
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy only the virtualenv from builder (not Poetry itself)
COPY --from=builder /builder/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source code
COPY app/ ./app/
COPY tests/ ./tests/

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]