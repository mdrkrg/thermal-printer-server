FROM docker.io/library/python:3.14-alpine

WORKDIR /app

ARG UV_VERSION=0.11

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Disable development dependencies
ENV UV_NO_DEV=1

RUN --mount=from=ghcr.io/astral-sh/uv:$UV_VERSION,source=/uv,target=/bin/uv \
  --mount=type=bind,source=uv.lock,target=uv.lock \
  --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv sync --locked --no-install-project

COPY . /app

RUN --mount=from=ghcr.io/astral-sh/uv:$UV_VERSION,source=/uv,target=/bin/uv \
  --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "main.py"]
