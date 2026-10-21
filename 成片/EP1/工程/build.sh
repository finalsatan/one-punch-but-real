#!/usr/bin/env bash
# EP1 动态漫画一键构建。用法：build.sh [镜号...]  （带镜号只重渲这些镜头）
# 依赖：ffmpeg（含 libass）、python3 venv 内的 edge-tts / numpy / scipy，字体 ZCOOL KuaiLe、ZCOOL QingKe HuangYou
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python3}
OUT=../EP1-一拳超人是假的一击KO是真的.mp4

$PY tts.py >/dev/null                 # 配音（已有的不重复生成）
if [ $# -gt 0 ]; then python3 render.py "$@"; fi
python3 render.py --concat-only       # 按当前时间轴拼接全部镜头（缺的镜头会补渲）
$PY audio.py                          # 配乐 + 音效 + 配音混音
python3 subs.py                       # 字幕与字卡

ffmpeg -loglevel error -y -i build/video.mp4 -i build/mix.wav \
  -vf "subtitles=build/subs.ass" \
  -af "loudnorm=I=-14:TP=-1.5:LRA=9" -ar 48000 \
  -c:v libx264 -preset medium -crf 19 -profile:v high -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 192k -shortest "$OUT"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT"
