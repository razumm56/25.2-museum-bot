FROM python:3.12-slim AS build

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

ENV UV_PYTHON="python"

RUN uv sync --frozen 

COPY . .

FROM build

WORKDIR /app

COPY --from=build . .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uv", "run" ,"-m" ,"ai_museum"]
