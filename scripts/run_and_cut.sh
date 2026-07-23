#!/bin/bash
# 用法: bash run_and_cut.sh <source名> <目标B tokens>
# 例:   bash run_and_cut.sh CC_head 10
SRC=$1
TARGET_B=$2
BASE=/mnt/si0024814o4k/ckbzzb/public/Dolma1.7_full
OUT=/mnt/si0024814o4k/ckbzzb/personal/xiesiwei/tokenized/Dolma1.7_tokenized
LOGDIR=/mnt/si0024814o4k/ckbzzb/personal/xiesiwei/logs
LOG="$LOGDIR/tokenize_${SRC}.log"

setsid dolma tokens \
  --documents "$BASE/$SRC/documents" \
  --destination "$OUT/$SRC" \
  --max_size 268435456 \
  --tokenizer.name_or_path 'Qwen/Qwen2-1.5B' \
  --tokenizer.eos_token_id 151643 \
  --tokenizer.pad_token_id 151643 \
  --processes 80 \
  --dtype "uint32" \
  > "$LOG" 2>&1 &
PID=$!

while kill -0 $PID 2>/dev/null; do
  CUR=$(tr '\r' '\n' < "$LOG" 2>/dev/null | grep -oP 'tokens:\s*\K[0-9.]+[GMk]?t(?=\s*\[)' | tail -1)
  DONE=$(echo "$CUR" | awk '{v=$1; sub(/t$/,"",v); u=substr(v,length(v),1); n=substr(v,1,length(v)-1)+0; if(u=="G")n*=1e9; else if(u=="M")n*=1e6; else if(u=="k")n*=1e3; if(u~/[0-9]/)n=v+0; print n}')
  if [ -n "$DONE" ] && awk "BEGIN{exit !($DONE >= $TARGET_B*1e9)}"; then
    echo "$(date) $SRC 达到 $CUR，截断"
    kill -INT -- -$PID
    sleep 10
    kill -0 $PID 2>/dev/null && kill -TERM -- -$PID
    break
  fi
  sleep 60
done
wait $PID 2>/dev/null
echo "$(date) $SRC 结束"
