#!/bin/bash
# 泽龙中转站 grok-video 图生视频(i2v) — 同步端点 /v1/created/video
# 用法: ./grok_i2v_run.sh <参考图> "<英文prompt>" <输出名> [seconds] [resolution_name] [size]
set -u
DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "$DIR/secret.zelong.env"
H="Authorization: Bearer $ZKEY"
IMG="$1"; PROMPT="$2"; NAME="$3"; SEC="${4:-6}"; RES="${5:-720p}"; SIZE="${6:-720x1280}"
OUT="$DIR/output"; LOG="$OUT/${NAME}.log"; mkdir -p "$OUT"
echo "START $(date '+%H:%M:%S') model=grok-video img=$IMG sec=$SEC res=$RES size=$SIZE" > "$LOG"

# 1) 同步创建（grok-video 渲染完才返回 content_url）
R=$(curl -s --noproxy "*" --max-time 600 -X POST "$ZURL/v1/created/video" -H "$H" \
    -F "model=grok-video" -F "prompt=$PROMPT" -F "seconds=$SEC" \
    -F "resolution_name=$RES" -F "size=$SIZE" \
    -F "input_reference[]=@$IMG;type=image/jpeg")
echo "[resp] $(echo "$R" | head -c 500)" >> "$LOG"

CURL_PATH=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin).get('content_url',''))" 2>/dev/null)
if [ -z "$CURL_PATH" ]; then
  echo "CREATE_FAILED 无 content_url" >> "$LOG"; echo "FAILED $NAME"; exit 1
fi
echo "[ok] content_url=$CURL_PATH" >> "$LOG"

# 2) 下载
curl -s --noproxy "*" --max-time 300 -L "$ZURL$CURL_PATH" -H "$H" -o "$OUT/${NAME}.mp4" \
  -w "[download HTTP:%{http_code} size:%{size_download}]\n" >> "$LOG"
if file "$OUT/${NAME}.mp4" | grep -qi "ISO Media"; then
  echo "DONE $(date '+%H:%M:%S') -> output/${NAME}.mp4" >> "$LOG"; echo "DONE $NAME"
else
  echo "DOWNLOAD_BAD 非视频文件: $(head -c 200 "$OUT/${NAME}.mp4")" >> "$LOG"; echo "BAD $NAME"; exit 3
fi
