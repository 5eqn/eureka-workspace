FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
ENV MUJOCO_GL=osmesa

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    build-essential \
    cmake \
    pkg-config \
    python3 \
    python3-dev \
    python3-pip \
    liblcm-dev \
    libgl1 \
    libosmesa6 \
    libglfw3 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir \
    imageio \
    imageio-ffmpeg \
    lcm \
    matplotlib \
    mujoco \
    numpy \
    pandas \
    pillow \
    pyyaml \
    scipy

WORKDIR /workspace/eureka-workspace

COPY thirdparties/DrEureka /workspace/thirdparties/DrEureka
COPY scripts /workspace/eureka-workspace/scripts
