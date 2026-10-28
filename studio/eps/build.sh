#!/bin/bash
set -e
B=${REMOTION_BROWSER:-/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell}; BX=""; [ -x "$B" ] && BX="--browser-executable=$B"
D=/home/claude/eps/$1
python3 /home/claude/eps/mix_ep.py $D
cd /home/claude/rv
npx remotion render src/index.ts ${COMP:-Ep} $D/video.mp4 --props=$D/props.json $BX --concurrency=2 --muted --log=error
ffmpeg -v error -y -i $D/video.mp4 -i $D/mix.wav -map 0:v -map 1:a -c:v libx264 -crf 19 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -ar 44100 -shortest -movflags +faststart $D/final.mp4
echo DONE $1
