#!/bin/bash
# Seedance 2.0 图生视频(i2v) 一条龙：撞通道→创建→轮询→下载
# 用法: ./seedance_i2v_run.sh <参考图路径> "<英文prompt>" <输出名> [seconds] [size]
set -u
DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$DIR/secret.env"
H="Authorization: Bearer $ZDC_KEY"
IMG="$1"; PROMPT="$2"; NAME="$3"; SEC="${4:-4}"; SIZE="${5:-720x1280}"
OUT="$DIR/output"; LOG="$OUT/${NAME}.log"
echo "START $(date '+%H:%M:%S') img=$IMG sec=$SEC size=$SIZE" > "$LOG"

# 1) 撞通道创建（最多 40 次）
TID=""
for i in $(seq 1 40); do
  R=$(curl -s --max-time 120 -X POST "$ZDC_URL/v1/videos" -H "$H" \
      -F "model=seedance-2-0" -F "prompt=$PROMPT" -F "seconds=$SEC" -F "size=$SIZE" \
      -F "input_reference=@$IMG;type=image/jpeg")
  TID=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
  if [ -n "$TID" ]; then echo "[create#$i] OK task=$TID" >> "$LOG"; break; fi
  echo "[create#$i] $(echo "$R"|head -c 90)" >> "$LOG"; sleep 7
done
[ -z "$TID" ] && { echo "CREATE_FAILED 通道一直没起来" >> "$LOG"; exit 1; }

# 2) 轮询（最多 ~12 分钟）
for i in $(seq 1 60); do
  R=$(curl -s --max-time 30 "$ZDC_URL/v1/videos/$TID" -H "$H")
  ST=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
  echo "[poll#$i] $ST" >> "$LOG"
  case "$ST" in
    completed|succeeded|success) echo "$R" > "$OUT/${NAME}.task.json"; break;;
    failed|error) echo "RENDER_FAILED $(echo "$R"|head -c 200)" >> "$LOG"; exit 2;;
  esac
  sleep 12
done

# 3) 下载
curl -s --max-time 180 -L "$ZDC_URL/v1/videos/$TID/content" -H "$H" -o "$OUT/${NAME}.mp4" \
  -w "[download HTTP:%{http_code} size:%{size_download}]\n" >> "$LOG"
if file "$OUT/${NAME}.mp4" | grep -qi "ISO Media"; then
  echo "DONE $(date '+%H:%M:%S') -> output/${NAME}.mp4" >> "$LOG"
else
  echo "DOWNLOAD_BAD 非视频文件" >> "$LOG"; exit 3
fi
