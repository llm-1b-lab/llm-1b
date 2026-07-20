# 使用官方CUDA基础镜像（包含Python但未预装pip）
FROM nvidia/cuda:12.1.1-base-ubuntu22.04

# 1. 安装系统依赖（包括Python3和pip）
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 升级pip并设置工作目录
RUN python3 -m pip install --upgrade pip && \
    mkdir -p /workspace && \
    chmod 777 /workspace

# 3. wandb key（安全实践）
ENV WANDB_API_KEY=$WANDB_API_KEY # 将wandb key粘贴在这里作为环境变量

# 4. 克隆OLMo代码
WORKDIR /workspace
RUN git clone https://github.com/allenai/OLMo.git && cd OLMo && git checkout main

# 5. 安装项目依赖（分步操作便于缓存）
WORKDIR /workspace/OLMo

# 5.1 安装wandb并登录（仅在API_KEY存在时）
RUN if [ -n "$WANDB_API_KEY" ]; then \
        pip install wandb && \
        wandb login --relogin $WANDB_API_KEY; \
fi

# 5.2 安装包 指定torch版本
RUN pip install -e ".[all]" torch==2.6.0 -f https://download.pytorch.org/whl/torch_stable.html

# 6. 验证环境
RUN python3 -c "\
import torch; \
print(f'PyTorch版本: {torch.__version__}'); \
print(f'CUDA可用: {torch.cuda.is_available()}')"

RUN sleep 10

# 7. 清理缓存（减小镜像体积）
RUN rm -rf /root/.cache/pip && \
    find /usr -name '__pycache__' -exec rm -rf {} +

# (可选)创建日期
# RUN echo 'Rebuild at Tue Apr 29 19:10:10 CST 2025' > /build_time

# 8. 容器启动命令
CMD ["/bin/bash"]
