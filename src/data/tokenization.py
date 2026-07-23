"""
语料 Tokenization 模块

基于 Dolma 工具对原始语料进行分词处理。
支持两种模式：
  1. 全量 tokenize：适用于小规模高质量语料（wiki、Books 等）
  2. 预算截断 tokenize：适用于大规模语料（CC、C4 等），达到目标 token 量后自动中断

使用前需安装 dolma：
    pip install dolma==1.2.1

CLI 使用示例：
    # 全量 tokenize 单个 source
    dolma tokens \
      --documents "/path/to/documents" \
      --destination "/path/to/output" \
      --max_size 1073741824 \
      --tokenizer.name_or_path 'Qwen/Qwen2-1.5B' \
      --tokenizer.eos_token_id 151643 \
      --tokenizer.pad_token_id 151643 \
      --processes 80 \
      --dtype "uint32"
"""

import os
import subprocess
import logging

logger = logging.getLogger(__name__)

# 默认 tokenizer 配置
DEFAULT_TOKENIZER_NAME = "Qwen/Qwen2-1.5B"
DEFAULT_EOS_TOKEN_ID = 151643
DEFAULT_PAD_TOKEN_ID = 151643
DEFAULT_DTYPE = "uint32"


def tokenize_source(
    documents_path: str,
    destination_path: str,
    max_size: int = 1073741824,
    tokenizer_name: str = DEFAULT_TOKENIZER_NAME,
    eos_token_id: int = DEFAULT_EOS_TOKEN_ID,
    pad_token_id: int = DEFAULT_PAD_TOKEN_ID,
    processes: int = 80,
    dtype: str = DEFAULT_DTYPE,
) -> None:
    """
    对单个 source 执行全量 tokenization。

    Args:
        documents_path:  原始文档路径
        destination_path: tokenize 结果输出路径
        max_size:         单个 shard 最大字节数（默认 1GB）
        tokenizer_name:   HuggingFace tokenizer 名称或路径
        eos_token_id:     EOS token ID
        pad_token_id:     PAD token ID
        processes:        并行进程数
        dtype:            输出数据类型（"uint32" 或 "uint16"）
    """
    cmd = [
        "dolma", "tokens",
        "--documents", documents_path,
        "--destination", destination_path,
        "--max_size", str(max_size),
        "--tokenizer.name_or_path", tokenizer_name,
        "--tokenizer.eos_token_id", str(eos_token_id),
        "--tokenizer.pad_token_id", str(pad_token_id),
        "--processes", str(processes),
        "--dtype", dtype,
    ]

    logger.info(f"执行 tokenization: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    logger.info(f"Tokenization 完成: {destination_path}")


def tokenize_selected_sources(
    base_path: str,
    output_base: str,
    sources: list,
    log_dir: str,
    max_size: int = 1073741824,
    processes: int = 80,
) -> None:
    """
    对多个 source 依次执行全量 tokenization。
    对应 scripts/tokenize_selected_sources.sh 的 Python 版本。

    Args:
        base_path:   文档根目录（如 /mnt/.../Dolma1.7_full）
        output_base: tokenize 输出根目录
        sources:     要处理的 source 名称列表
        log_dir:     日志输出目录
        max_size:    单个 shard 最大字节数
        processes:   并行进程数
    """
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(output_base, exist_ok=True)

    for name in sources:
        src = os.path.join(base_path, name, "documents")
        dst = os.path.join(output_base, name)

        if not os.path.isdir(src):
            logger.warning(f"跳过 {name}: 路径不存在 {src}")
            continue
        if os.path.isdir(dst):
            logger.warning(f"跳过 {name}: 输出目录已存在 {dst}")
            continue

        logger.info(f"=== tokenizing {name} start ===")
        tokenize_source(
            documents_path=src,
            destination_path=dst,
            max_size=max_size,
            processes=processes,
        )
        logger.info(f"=== tokenizing {name} done ===")


def validate_shards(destination_path: str) -> tuple[int, int]:
    """
    验证 tokenized 分片文件的完好性。

    检查每个 .npy 文件的：
      1. 文件大小 > 0 且能被 4 整除（uint32 = 4 字节）
      2. 内容不全为零（空壳占位文件）

    Args:
        destination_path: tokenize 输出目录

    Returns:
        (total_files, total_tokens) 元组
    """
    import glob

    files = sorted(glob.glob(os.path.join(destination_path, "*.npy")))
    bad = []
    total = 0

    for f in files:
        try:
            sz = os.path.getsize(f)
            assert sz > 0 and sz % 4 == 0, "size异常"

            import numpy as np
            a = np.memmap(f, dtype=np.uint32, mode="r")
            n = a.shape[0]

            # 抽头/中/尾三段各1000个token，全为0则是空壳占位文件
            samples = list(a[:1000]) + list(a[n // 2 : n // 2 + 1000]) + list(a[-1000:])
            assert sum(samples) > 0, "全零空壳"

            total += n
        except Exception as e:
            bad.append((f, str(e)))

    logger.info(f"{len(files)} 个分片, {total / 1e9:.2f}B tokens")
    if bad:
        logger.warning(f"问题文件: {bad}")
        for f, _ in bad:
            os.remove(f)
            logger.info(f"已删除: {f}")
    else:
        logger.info("全部完好")

    return len(files), total


def tokenize_with_budget(
    source_name: str,
    base_path: str,
    output_base: str,
    target_billion_tokens: float,
    log_dir: str,
    max_size: int = 268435456,
    processes: int = 80,
) -> None:
    """
    对单个 source 执行 tokenization，达到目标 token 量后自动截断。
    对应 scripts/run_and_cut.sh 的 Python 版本。

    通过实时监控 dolma 输出日志中的 token 计数，
    当累计 token 数达到目标值（target_billion_tokens * 10^9）时，
    向 dolma 进程发送 SIGINT 终止。

    Args:
        source_name:            source 名称（如 "CC_head"）
        base_path:              文档根目录
        output_base:            tokenize 输出根目录
        target_billion_tokens:  目标 token 量（单位：B / 10^9）
        log_dir:                日志输出目录
        max_size:               单个 shard 最大字节数（默认 256MB）
        processes:              并行进程数
    """
    import signal
    import time
    import re

    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(output_base, exist_ok=True)

    src = os.path.join(base_path, source_name, "documents")
    dst = os.path.join(output_base, source_name)
    log_file = os.path.join(log_dir, f"tokenize_{source_name}.log")

    target_tokens = int(target_billion_tokens * 1e9)

    cmd = [
        "dolma", "tokens",
        "--documents", src,
        "--destination", dst,
        "--max_size", str(max_size),
        "--tokenizer.name_or_path", DEFAULT_TOKENIZER_NAME,
        "--tokenizer.eos_token_id", str(DEFAULT_EOS_TOKEN_ID),
        "--tokenizer.pad_token_id", str(DEFAULT_PAD_TOKEN_ID),
        "--processes", str(processes),
        "--dtype", DEFAULT_DTYPE,
    ]

    logger.info(f"执行 tokenization (target={target_billion_tokens}B): {' '.join(cmd)}")

    with open(log_file, "w") as log_fh:
        proc = subprocess.Popen(
            cmd,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setpgrp,  # 创建新进程组，便于 kill 整个进程树
        )

    # 监控日志中的 token 计数
    token_pattern = re.compile(r"tokens:\s*([0-9.]+[GMk]?)t?\s*\[")

    while proc.poll() is None:
        try:
            with open(log_file, "r") as f:
                content = f.read()
        except Exception:
            time.sleep(60)
            continue

        matches = token_pattern.findall(content)
        if matches:
            last = matches[-1]
            done = _parse_token_count(last)
            if done is not None and done >= target_tokens:
                logger.info(f"{source_name} 达到 {last}，截断")
                os.killpg(os.getpgid(proc.pid), signal.SIGINT)
                time.sleep(10)
                if proc.poll() is None:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                break

        time.sleep(60)

    proc.wait()
    logger.info(f"{source_name} tokenization 结束")


def decode_sample(npy_path: str, n_tokens: int = 80) -> str:
    """
    从 tokenized .npy 文件中解码一段 token 为文本，用于抽验 tokenization 质量。

    Args:
        npy_path: .npy 文件路径
        n_tokens: 要解码的 token 数量（默认 80）

    Returns:
        解码后的文本字符串
    """
    import numpy as np
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(DEFAULT_TOKENIZER_NAME)
    a = np.memmap(npy_path, dtype=np.uint32, mode="r")
    text = tok.decode(a[:n_tokens].tolist())
    logger.info(f"Decode {n_tokens} tokens from {npy_path}:\n{text}")
    return text


def count_tokens(output_base: str) -> dict:
    """
    统计每个 source 目录下的 token 总量。

    Args:
        output_base: tokenized 输出根目录

    Returns:
        {source_name: token_count} 字典，含 "TOTAL" 汇总键
    """
    import glob

    result = {}
    total_all = 0

    for d in sorted(glob.glob(os.path.join(output_base, "*"))):
        files = glob.glob(os.path.join(d, "*.npy"))
        tokens = 0
        for f in files:
            sz = os.path.getsize(f)
            if sz % 4 != 0:
                logger.warning(f"字节数不是4的倍数: {f}")
            tokens += sz // 4
        total_all += tokens
        name = os.path.basename(d)
        result[name] = tokens
        logger.info(f"{name:18s} {tokens / 1e9:7.2f}B tokens  ({len(files)} shards)")

    result["TOTAL"] = total_all
    logger.info(f"{'TOTAL':18s} {total_all / 1e9:7.2f}B tokens")
    return result


def _parse_token_count(token_str: str) -> int | None:
    """解析 dolma 输出的 token 计数字符串，如 '1.5Gt' -> 1500000000"""
    import re

    m = re.match(r"([0-9.]+)\s*([GMk])?", token_str)
    if not m:
        return None

    value = float(m.group(1))
    unit = m.group(2)

    if unit == "G":
        value *= 1e9
    elif unit == "M":
        value *= 1e6
    elif unit == "k":
        value *= 1e3

    return int(value)
