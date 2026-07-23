"""
语料数据下载模块

通过海纳数据平台（haina-datahub）CLI 下载原始语料数据集。
使用前需配置环境变量：
    export HAINA_DATAHUB_AK=<access_key>
    export HAINA_DATAHUB_SK=<secret_key>

CLI 使用示例：
    haina-datahub dataset download \
        --dataset-repo zhangy/annas-archive-result1 \
        --target-path /mnt/si0024814o4k/ckbzzb/public/annas-archive-result1
"""

import os
import subprocess
import logging

logger = logging.getLogger(__name__)


def download_dataset(dataset_repo: str, target_path: str) -> None:
    """
    从海纳平台下载数据集。

    Args:
        dataset_repo: 数据集仓库路径，格式 "<user>/<repo>"
                       例如 "zhangy/annas-archive-result1"
        target_path: 本地存储路径
    """
    ak = os.environ.get("HAINA_DATAHUB_AK")
    sk = os.environ.get("HAINA_DATAHUB_SK")

    if not ak or not sk:
        raise RuntimeError(
            "请设置环境变量 HAINA_DATAHUB_AK 和 HAINA_DATAHUB_SK"
        )

    cmd = [
        "haina-datahub", "dataset", "download",
        "--dataset-repo", dataset_repo,
        "--target-path", target_path,
    ]

    logger.info(f"执行下载命令: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    logger.info(f"数据集已下载到: {target_path}")
