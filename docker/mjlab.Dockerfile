FROM nvidia/cuda:12.8.0-runtime-ubuntu24.04
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_PREFERENCE=only-managed
ENV UV_PYTHON_INSTALL_DIR=/opt/uv/python
ENV MUJOCO_GL=egl

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    curl \
    libegl-dev \
    libgl1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN uv python install 3.13

WORKDIR /workspace/thirdparties/MJLab
COPY thirdparties/DrEureka /workspace/thirdparties/DrEureka
COPY thirdparties/MJLab /workspace/thirdparties/MJLab

RUN uv sync --locked --no-editable --no-dev

WORKDIR /workspace/eureka-workspace
COPY scripts /workspace/eureka-workspace/scripts
