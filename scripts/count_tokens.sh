#!/bin/bash
# 用法: bash count_tokens.sh <tokenized根目录>
# 例:   bash count_tokens.sh /mnt/.../Dolma1.7_tokenized
OUT="${1:-/mnt/si0024814o4k/ckbzzb/personal/xiesiwei/tokenized/Dolma1.7_tokenized}"
if [ ! -d "$OUT" ]; then
  echo "用法: bash count_tokens.sh <tokenized根目录>"
  exit 1
fi

python3 -c "
import glob, os, sys
OUT = sys.argv[1]
total_all = 0
for d in sorted(glob.glob(f'{OUT}/*')):
    files = glob.glob(f'{d}/*.npy')
    tokens, warn = 0, []
    for f in files:
        sz = os.path.getsize(f)
        if sz % 4 != 0:
            warn.append(f)
        tokens += sz // 4
    total_all += tokens
    name = os.path.basename(d)
    print(f'{name:18s} {tokens/1e9:7.2f}B tokens  ({len(files)} shards)')
    for f in warn:
        print(f'  ⚠️  字节数不是4的倍数: {f}')
print(f'{\"TOTAL\":18s} {total_all/1e9:7.2f}B tokens')
" "$OUT"
