# AGENT_RULES.md — llm-1b 开发规范

本文件是 AI Agent 与人类开发者在本仓库中协作时必须遵守的强制性规范。所有规则适用于 `feature/*`、`fix/*`、`docs/*` 等非主分支；`main` 分支受保护，禁止直接推送。

---

## 1. Git 纪律

### 1.1 分支命名

- 功能开发：`feature/<简短描述>`，如 `feature/add-tokenizer`
- 缺陷修复：`fix/<简短描述>`，如 `fix-oom-in-dataloader`
- 文档/配置：`docs/<简短描述>`，如 `docs-readme-setup`
- 描述使用小写英文，单词间用连字符 `-` 分隔

### 1.2 禁止直接推送 main

`main` 分支受保护，所有变更必须通过 Pull Request 合并。禁止执行以下操作：

- `git push origin main`
- `git push --force origin main`
- 在 `main` 分支上直接 `git commit`

### 1.3 Commit 规范

- 提交信息格式：`<type>: <简短描述>`
  - `feat:` — 新功能
  - `fix:` — 缺陷修复
  - `docs:` — 文档变更
  - `refactor:` — 重构（无功能变化）
  - `chore:` — 构建、CI、依赖等杂项
  - `test:` — 测试相关
- 描述使用中文或英文均可，但同一 PR 内保持一致
- 一次 commit 只做一件事，保持原子性

### 1.4 **强制条款：即时提交**

> **每次完成任何代码修改（包括新增、删除、重构、修复），必须立即执行 `git add` + `git commit`，禁止累积多个改动后一次性提交。**
>
> - 每完成一个独立的逻辑变更，立即提交
> - 不允许等到"功能做完了"再统一提交
> - 不允许跨文件批量提交不相关的改动
> - 如果一次修改涉及多个文件但属于同一个逻辑变更，可以在一个 commit 中提交
> - WIP（Work In Progress）提交是允许且鼓励的，后续可通过 `git rebase -i` 整理

---

## 2. 环境即代码

### 2.1 requirements.txt 版本锁定

本仓库使用 `requirements.txt` 管理 Python 依赖。文件位于仓库根目录。

**依赖声明规则：**

- 所有直接依赖写入 `requirements.txt`，每行一个包
- 版本号使用精确版本（`==`），不允许使用 `>=`、`~=` 或不写版本号
- 示例格式：
  ```
  torch==2.6.0
  wandb==0.19.0
  transformers==4.48.0
  ```
- 间接依赖（由直接依赖自动安装的包）不需要写入
- `requirements.txt` 按字母顺序排列，便于查找

### 2.2 pip 安装规范

服务器为 Kubernetes 容器环境，**没有 Docker 运行时和 apt 包管理器**，依赖安装方式：

```bash
python3 -m pip install -r requirements.txt
```

### 2.3 **强制条款：环境同步**

> **1. 每次引入新的 Python 包（pip install）或修改依赖版本，必须同步更新 `requirements.txt` 并写入精确版本号（`==X.Y.Z`）。**
>
> **2. 每次修改系统级配置或运行环境，必须同步维护 `docker/Dockerfile`，确保 Docker 镜像构建与环境定义一致。**
>
> **3. 禁止在代码中使用未在 `requirements.txt` 中声明的依赖。**
>
> - 添加新依赖后，运行 `python3 -m pip freeze | grep <包名>` 获取精确版本号
> - 验证方式：在干净环境中执行 `python3 -m pip install -r requirements.txt`，确保所有导入成功
> - `requirements.txt` 的变更必须作为独立 commit 或在引入该依赖的同一 commit 中提交

### 2.4 Docker 镜像

- Dockerfile 位于 `docker/Dockerfile`
- 基础镜像：`nvidia/cuda:12.1.1-base-ubuntu22.04`
- 镜像推送到 GitHub Container Registry (`ghcr.io`)
- CI 触发条件：`docker/Dockerfile`、`.dockerignore`、`.github/workflows/docker-image.yml` 变更时自动构建
- 注意：K8s 运行环境不支持 Docker 构建，镜像构建由 GitHub Actions 完成

---

## 3. 测试纪律

### 3.1 测试文件位置

- 所有测试文件放在 `tests/` 目录下，目录结构镜像 `src/` 结构
- 测试文件命名：`test_<被测模块名>.py`
- 示例结构：
  ```
  tests/
  ├── __init__.py
  ├── test_data_loader.py
  ├── test_model.py
  └── test_tokenizer.py
  ```

### 3.2 测试框架

- 使用 `pytest` 作为测试框架
- 测试依赖应在 `requirements.txt` 中显式声明（如 `pytest==8.x.x`）

### 3.3 运行方式

```bash
# 运行全部测试
python3 -m pytest tests/

# 运行指定测试文件
python3 -m pytest tests/test_data_loader.py

# 带详细输出
python3 -m pytest tests/ -v

# 带覆盖率报告
python3 -m pytest tests/ --cov=src/ --cov-report=term-missing
```

### 3.4 测试纪律

- 新增功能必须同时编写对应测试
- 修复 bug 必须先编写能复现问题的测试，再修复
- 测试不应依赖外部网络或特定硬件（如 GPU）
- 测试应可在 CI 环境中独立运行，不依赖本地文件路径
- PR 合并前确保所有测试通过

---

## 4. 代码规范

### 4.1 目录结构

代码当前处于早期阶段，建议的目录结构如下（随项目发展逐步建立）：

```
llm-1b/
├── src/                # 源代码
│   ├── __init__.py
│   ├── data/           # 数据处理
│   ├── model/          # 模型定义
│   ├── training/       # 训练逻辑
│   └── utils/          # 工具函数
├── tests/              # 测试
├── configs/            # 配置文件（YAML/JSON）
├── scripts/            # 启动脚本
├── docker/             # Docker 相关
│   └── Dockerfile
├── requirements.txt    # Python 依赖
└── README.md
```

### 4.2 路径与配置

- **禁止硬编码路径**：代码中不得出现绝对路径（如 `/home/user/data` 或 `/workspace/OLMo`）
- 所有路径通过以下方式获取：
  - 环境变量，如 `os.environ.get("DATA_DIR", "./data")`
  - 命令行参数，如 `argparse`
  - 配置文件，如 YAML config
  - 相对路径（相对于项目根目录）
- 配置优先级：命令行参数 > 环境变量 > 配置文件默认值

### 4.3 环境变量命名

- 使用 `UPPER_SNAKE_CASE` 命名
- 使用项目前缀 `LLM1B_` 避免与其他系统冲突
- 示例：
  ```python
  LLM1B_DATA_DIR=/mnt/data
  LLM1B_MODEL_DIR=/mnt/models
  LLM1B_LOG_LEVEL=INFO
  WANDB_API_KEY=<key>
  ```

### 4.4 代码风格

- 遵循 PEP 8
- 使用 `ruff` 或 `flake8` 进行静态检查（开发依赖）
- 类型注解推荐但非强制

---

## 5. 服务器运行规范

### 5.1 环境说明

- **运行环境**：Kubernetes 容器
- **无 Docker**：容器内不支持 Docker 运行时
- **无 apt**：容器内不支持 apt 包管理器
- **Python 版本**：Python 3（通过 `python3` 调用）
- **GPU**：支持 CUDA 12.1

### 5.2 依赖安装

```bash
# 基本安装
python3 -m pip install -r requirements.txt

# 需要升级 pip 时
python3 -m pip install --upgrade pip
```

### 5.3 脚本运行

```bash
# 运行 Python 脚本
python3 scripts/train.py --config configs/experiment.yaml

# 运行模块
python3 -m src.training.train --config configs/experiment.yaml

# 运行测试
python3 -m pytest tests/
```

### 5.4 注意事项

- 始终使用 `python3` 而非 `python`
- 始终使用 `python3 -m pip` 而非直接 `pip`，确保 pip 与当前 Python 解释器对应
- 不要假设容器内有 `sudo` 权限
- 不要在容器内修改系统级 Python 包
- wandb API key 通过环境变量 `WANDB_API_KEY` 传入，禁止写入代码或配置文件
- 所有持久化数据写入挂载卷路径，不写入容器临时文件系统

---

## 6. 禁止提交的内容

以下内容**绝对禁止**提交到仓库（已在 `.gitignore` 中配置）：

- API 密钥、云凭据、SSH 密钥、Token、`.env` 文件
- 原始数据集和私有数据
- 模型检查点（`.pt`、`.pth`、`.bin`、`.safetensors`、`.ckpt` 等）
- 优化器状态、TensorBoard 日志、wandb 运行记录
- 大型二进制文件（应使用 Git LFS 或外部存储）

---

*本文件随项目演进持续更新。任何规则的修改需要提交 PR 并经代码审查。*
