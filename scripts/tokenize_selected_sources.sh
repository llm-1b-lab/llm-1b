#!/bin/bash
# tokenize_selected_sources.sh
# Dolma 1.7 选中 source 的 tokenization，~60B token 训练预算的语料准备

BASE=/mnt/si0024814o4k/ckbzzb/public/Dolma1.7_full
OUT=/mnt/si0024814o4k/ckbzzb/personal/xiesiwei/tokenized/Dolma1.7_tokenized
LOGDIR=/mnt/si0024814o4k/ckbzzb/personal/xiesiwei/logs

mkdir -p "$LOGDIR"

# 顺序：小的高质量源优先，大源手动（可按配比中断）
SOURCES=(wiki OpenWebMath AlgebraicStack StackExchange Books Arxiv pes2o)

for name in "${SOURCES[@]}"; do
  src="$BASE/$name/documents"
  if [ ! -d "$src" ]; then
    echo "=== SKIP $name: $src 不存在 ===" | tee -a "$LOGDIR/tokenize_all.log"
    continue
  fi
  if [ -d "$OUT/$name" ]; then
    echo "=== SKIP $name: 输出目录已存在 ===" | tee -a "$LOGDIR/tokenize_all.log"
    continue
  fi

  echo "=== tokenizing $name  start: $(date) ===" | tee -a "$LOGDIR/tokenize_all.log"

  dolma tokens \
    --documents "$src" \
    --destination "$OUT/$name" \
    --max_size 1073741824 \
    --tokenizer.name_or_path 'Qwen/Qwen2-1.5B' \
    --tokenizer.eos_token_id 151643 \
    --tokenizer.pad_token_id 151643 \
    --processes 80 \
    --dtype "uint32" \
    2>&1 | tee "$LOGDIR/tokenize_${name}.log"

  echo "=== done $name  end: $(date) ===" | tee -a "$LOGDIR/tokenize_all.log"
done

echo "=== ALL FINISHED: $(date) ===" | tee -a "$LOGDIR/tokenize_all.log"
