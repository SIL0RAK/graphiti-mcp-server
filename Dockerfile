FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN pip install --upgrade pip uv

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev

COPY . .

EXPOSE 8000

CMD ["python", "-m", "server"]
