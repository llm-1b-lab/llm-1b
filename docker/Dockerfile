# 使用官方CUDA基础镜像（包含Python但未预装pip）
FROM nvidia/cuda:12.1.1-base-ubuntu22.04

# 1. 安装系统依赖（包括Python3和pip）
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 2. 配置 pip 清华镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 升级pip并设置工作目录
RUN python3 -m pip install --upgrade pip && \
    mkdir -p /workspace && \
    chmod 777 /workspace

# 4. 复制项目代码并安装依赖
WORKDIR /workspace
COPY requirements.txt /workspace/requirements.txt
RUN python3 -m pip install -r requirements.txt

COPY src/ /workspace/src/

# 5. wandb 在运行容器时通过环境变量传入 WANDB_API_KEY，不写入镜像层。

# 6. 验证环境
RUN python3 -c "\
import torch; \
print(f'PyTorch版本: {torch.__version__}'); \
print(f'CUDA可用: {torch.cuda.is_available()}')"

RUN sleep 10

# 7. 清理缓存（减小镜像体积）
RUN rm -rf /root/.cache/pip && \
    find /usr -name '__pycache__' -exec rm -rf {} +

# 8. 容器启动命令
CMD ["/bin/bash"]
