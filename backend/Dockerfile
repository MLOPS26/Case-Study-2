FROM python:3.12-slim

WORKDIR /opt/app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
COPY backend/ ./backend/

RUN uv sync --frozen --no-dev

RUN mkdir -p uploads db

EXPOSE 22092

CMD ["uv", "run", "fastapi", "run", "backend/routes.py", "--host", "0.0.0.0", "--port", "22092"]
