FROM python:3.12-slim AS build

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

ENV UV_PYTHON="python"

RUN uv sync --frozen --no-cache

FROM python:3.12-slim

WORKDIR /app

COPY --from=build /app/.venv /app/.venv/

ENV PATH="/app/.venv/bin:$PATH"

COPY . .

EXPOSE 8000

CMD ["python" ,"-m" ,"ai_museum"]
