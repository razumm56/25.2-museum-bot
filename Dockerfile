FROM python:3.12-slim

WORKDIR /app

RUN apt update && apt upgrade
RUN apt install -y build-essential

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

ENV UV_PYTHON="python"
RUN uv sync --locked --no-cache

COPY ./.env .
COPY ./ai_museum/ ./ai_museum
COPY ./temp/ ./temp
COPY ./data/ ./data

CMD ["uv", "run" ,"-m" ,"ai_museum"]
