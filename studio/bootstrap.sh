#!/bin/bash
# ШІкарно studio bootstrap — розгортає конвеєр відео в /home/claude з репозиторію shikarno-site/studio.
# Запуск: bash studio/bootstrap.sh   (ідемпотентний; секрети НЕ в репозиторії — див. крок secrets нижче)
set -e
REPO=$(cd "$(dirname "$0")/.." && pwd); S=$REPO/studio; H=/home/claude
mkdir -p $H
for d in rv eps tg yt gem pdf; do
  if [ ! -e $H/$d ]; then ln -s $S/$d $H/$d; fi
done
[ -e $H/asr.py ] || ln -s $S/asr.py $H/asr.py
mkdir -p $S/eps/thumbs
# Python залежності (без venv; st2env більше не потрібен — створюємо симлінк-заглушку для старих команд)
python3 -m pip install -q --break-system-packages numpy soundfile sherpa-onnx playwright >/dev/null 2>&1 || python3 -m pip install -q numpy soundfile sherpa-onnx playwright
mkdir -p $H/st2env/bin; [ -f $H/st2env/bin/activate ] || echo 'true' > $H/st2env/bin/activate
# Whisper для audit_vo/align (≈1.3 ГБ, тільки якщо немає)
if [ ! -f $H/sherpa-onnx-whisper-small/small-tokens.txt ]; then
  cd $H && curl -sSL -o w.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2 && tar xjf w.tar.bz2 && rm w.tar.bz2
fi
# ffmpeg
command -v ffmpeg >/dev/null || (apt-get update -qq && apt-get install -y -qq ffmpeg >/dev/null)
command -v pdftoppm >/dev/null || apt-get install -y -qq poppler-utils >/dev/null || true
# Remotion
cd $S/rv && [ -d node_modules ] || npm ci --silent
npx remotion browser ensure >/dev/null 2>&1 || true
python3 -m playwright install chromium >/dev/null 2>&1 || true
echo "BOOTSTRAP OK. Тепер секрети: $H/tg/.token, $H/gem/.key, $H/yt/client_secret.json, $H/yt/token.json (див. studio/MIGRATION.md)"
