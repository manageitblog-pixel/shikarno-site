#!/bin/bash
# Стійкий рендер 16:9 шматками по CH кадрів (переживає перезапуск контейнера: готові шматки пропускаються)
# usage: render_chunks.sh <dir> <composition> [CH]
set -e
B=${REMOTION_BROWSER:-/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell}; BX=""; [ -x "$B" ] && BX="--browser-executable=$B"
D=$1; COMP=$2; CH=${3:-900}
TOTAL=$(python3 -c "import json;print(json.load(open('$D/props.json'))['total'])")
mkdir -p $D/chunks; cd /home/claude/rv
for ((a=0; a<TOTAL; a+=CH)); do
  b=$((a+CH-1)); [ $b -ge $TOTAL ] && b=$((TOTAL-1))
  f=$D/chunks/c_$(printf %06d $a).mp4
  [ -s $f.ok ] && continue
  npx remotion render src/index.ts $COMP $f --props=$D/props.json --frames=$a-$b $BX --concurrency=2 --muted --log=error
  echo $a-$b > $f.ok; echo "chunk $a-$b done $(date -u +%H:%M)"
done
ls $D/chunks/c_*.mp4 | sort | sed "s/^/file '/;s/$/'/" > $D/chunks/list.txt
ffmpeg -v error -y -f concat -safe 0 -i $D/chunks/list.txt -c copy $D/video.mp4
echo CHUNKS_DONE
