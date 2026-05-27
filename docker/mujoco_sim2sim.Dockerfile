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
    libyaml-dev \
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

COPY thirdparties/cyclonedds /workspace/thirdparties/cyclonedds
RUN cmake -S /workspace/thirdparties/cyclonedds -B /tmp/cyclonedds-build \
      -DCMAKE_INSTALL_PREFIX=/opt/cyclonedds \
      -DBUILD_EXAMPLES=OFF \
      -DBUILD_TESTING=OFF \
    && cmake --build /tmp/cyclonedds-build --target install -j"$(nproc)" \
    && rm -rf /tmp/cyclonedds-build

ENV CYCLONEDDS_HOME=/opt/cyclonedds
ENV CMAKE_PREFIX_PATH=/opt/cyclonedds

COPY thirdparties/unitree_sdk2_python /workspace/thirdparties/unitree_sdk2_python
RUN python3 -m pip install --no-cache-dir --no-deps -e /workspace/thirdparties/unitree_sdk2_python \
    && python3 -m pip install --no-cache-dir cyclonedds==0.10.2 opencv-python-headless

WORKDIR /workspace/eureka-workspace

COPY thirdparties/DrEureka /workspace/thirdparties/DrEureka
COPY scripts /workspace/eureka-workspace/scripts
