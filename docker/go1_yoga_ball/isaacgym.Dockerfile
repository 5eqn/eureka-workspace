FROM pytorch/pytorch:1.10.0-cuda11.3-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
ENV LD_LIBRARY_PATH=/opt/conda/lib:/usr/local/nvidia/lib:/usr/local/nvidia/lib64

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    build-essential \
    liblcm-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libglfw3 \
    libgles2 \
    libosmesa6 \
    libx11-6 \
    libxcursor1 \
    libxext6 \
    libxi6 \
    libxinerama1 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir \
    pip==23.3.2 \
    setuptools==58.0.4 \
    wheel==0.37.1
RUN python -m pip install --no-cache-dir --timeout 120 --retries 10 \
    --trusted-host pypi.org \
    --trusted-host files.pythonhosted.org \
    gym==0.18.0 \
    hydra-core \
    matplotlib==3.5.3 \
    ml-logger==0.8.117 \
    params-proto==2.10.0 \
    tqdm \
    wandb==0.15.0 \
    wandb_osh \
    moviepy \
    imageio \
    lcm \
    opencv-python-headless==4.8.1.78

WORKDIR /workspace

COPY thirdparties/DrEureka /workspace/thirdparties/DrEureka
COPY thirdparties/IsaacGym /workspace/thirdparties/IsaacGym

RUN if [ -d /workspace/thirdparties/IsaacGym/python ]; then \
      python -m pip install -e /workspace/thirdparties/IsaacGym/python; \
    else \
      echo "Isaac Gym package not found at thirdparties/IsaacGym/python" >&2; \
      exit 1; \
    fi

RUN python -m pip install --no-deps -e /workspace/thirdparties/DrEureka \
    && python -m pip install --no-deps -e /workspace/thirdparties/DrEureka/globe_walking \
    && python -m pip install --no-deps -e /workspace/thirdparties/DrEureka/forward_locomotion \
    && python -m pip install --no-deps -e /workspace/thirdparties/DrEureka/globe_walking/go1_gym_deploy
