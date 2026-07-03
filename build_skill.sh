#!/usr/bin/env bash
# 把本仓库打包成 seedance-tryon-video.skill（可分发的技能包）。
# 打进包里的：SKILL.md、scripts/、references/（含示例素材）、agents/、docs/、requirements.txt。
# 不打进包：workspace/、99-敏感配置、.git 等（见 .gitignore）。
set -euo pipefail

cd "$(dirname "$0")"
NAME="seedance-tryon-video"
OUT_DIR="dist"
STAGE="$(mktemp -d)/$NAME"

mkdir -p "$STAGE" "$OUT_DIR"
cp SKILL.md requirements.txt "$STAGE"/
cp -R scripts references agents docs "$STAGE"/

# 清掉可能混入的缓存/系统文件
find "$STAGE" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$STAGE" -name '.DS_Store' -delete 2>/dev/null || true

OUT="$OUT_DIR/$NAME.skill"
rm -f "$OUT"
( cd "$(dirname "$STAGE")" && zip -r -q "$OLDPWD/$OUT" "$NAME" )
rm -rf "$(dirname "$STAGE")"

echo "已打包: $OUT"
unzip -l "$OUT" | tail -n +2 | head -40
