#!/bin/bash
# 用法: bash decode_sample.sh <npy文件路径> [解码token数量]
# 例:   bash decode_sample.sh /mnt/.../C4/part-00-00000.npy
#       bash decode_sample.sh /mnt/.../C4/part-00-00000.npy 100
NPY_FILE="$1"
N_TOKENS="${2:-80}"

if [ -z "$NPY_FILE" ] || [ ! -f "$NPY_FILE" ]; then
  echo "用法: bash decode_sample.sh <npy文件路径> [解码token数量，默认80]"
  exit 1
fi

python3 -c "
import numpy as np
from transformers import AutoTokenizer
import sys

tok = AutoTokenizer.from_pretrained('Qwen/Qwen2-1.5B')
a = np.memmap(sys.argv[1], dtype=np.uint32, mode='r')
n = int(sys.argv[2])
print(tok.decode(a[:n].tolist()))
" "$NPY_FILE" "$N_TOKENS"
