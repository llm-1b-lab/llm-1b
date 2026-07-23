#!/bin/bash
# 用法: bash validate_shards.sh <tokenized目录路径>
# 例:   bash validate_shards.sh /mnt/.../Dolma1.7_tokenized/C4
TARGET="$1"
if [ -z "$TARGET" ] || [ ! -d "$TARGET" ]; then
  echo "用法: bash validate_shards.sh <tokenized目录路径>"
  exit 1
fi

echo "$(date) 开始验证: $TARGET"

python3 -c "
import numpy as np, glob, os, sys
target = sys.argv[1]
files = sorted(glob.glob(f'{target}/*.npy'))
bad = []
total = 0
for f in files:
    try:
        sz = os.path.getsize(f)
        assert sz > 0 and sz % 4 == 0, 'size异常'
        a = np.memmap(f, dtype=np.uint32, mode='r')
        n = a.shape[0]
        samples = list(a[:1000]) + list(a[n//2:n//2+1000]) + list(a[-1000:])
        assert sum(samples) > 0, '全零空壳'
        total += n
    except Exception as e:
        bad.append((f, str(e)))
print(f'{len(files)} 个分片, {total/1e9:.2f}B tokens')
print('问题文件:', bad) if bad else print('全部完好')
for f, _ in bad:
    os.remove(f); print('已删除:', f)
" "$TARGET"

echo "$(date) 验证完成: $TARGET"
