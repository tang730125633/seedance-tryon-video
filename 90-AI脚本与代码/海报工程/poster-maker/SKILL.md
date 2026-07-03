---
name: poster-maker
description: 生成「国风课程招生长图海报」。改 config.json 的文案/价格/讲师，跑一条命令即出高清 PNG。文字精准、二维码真能扫、可无限复用。适合课程招生、活动、发布会等长图海报。任何 AI 照本说明填空即可，无需设计能力。
trigger: 招生海报、课程长图、活动海报、国风海报、做一张海报、poster
---

# poster-maker · 可复用国风招生长图海报

**核心思想**：设计已固化进模板，你只做「填空 + 跑命令」，不用懂代码、不用会设计。

## 三步出图

### 1. 改文案 → `config.json`
打开 `config.json`，按字段填你的内容（纯文本/价格/版块）。字段说明：
- `brand`：品牌名/副标/logo字
- `titlePre` / `titleBig` / `banner` / `desc`：主标题区（`titleBig` 里 `<em>xx</em>` = 红色书法强调）
- `speaker`：`img`=讲师照路径，`name`=`主讲：<b>名字</b>`
- `price` / `priceNow` / `priceInc`：价格条（每格带图标）
- `sections`：4 大版块，每个含 `no`(一二三四)、`t`(标题，`<em>`红字)、`intro`、`icon`、`pts`(要点数组)、`help`(["小标题",["箭头1","箭头2"]])
- `audience`：适合人群，每项 `["fa-图标名","文字"]`（图标用 Font Awesome 名，如 fa-user-tie/fa-industry/fa-store/fa-video）
- `gains`：你将获得（数组）
- `cta`：底部行动区（`qrData`=二维码扫码后打开的链接/文字）
- `slogan`：尾部口号

### 2.（可选）换讲师照 / 背景 → `ark_gen.py`
要换讲师立绘（用真人照生成西装立绘，保住本人脸）：
```bash
python3 ark_gen.py --out assets/speaker_final.png --ref /路径/你的真人照.jpg \
  --prompt "Professional waist-up portrait, dark navy business suit, arms crossed, confident, Chinese ink-wash mountain backdrop, photorealistic, keep face identical to reference"
# 生成图右下角有"AI生成"水印，裁掉底部一条：
ffmpeg -y -i assets/speaker_final.png -vf "crop=2048:1910:0:0" assets/speaker_final.png
```
然后把 `config.json` 的 `speaker.img` 指向它即可。背景同理（去掉 --ref，加 --size 1216x3072）。

### 3. 出图 → `make_poster.py`
```bash
python3 make_poster.py                      # config.json → poster.png
python3 make_poster.py config.json out.png  # 指定输入输出
```
得到一张 824 宽、2x 高清的长图 PNG。

## 依赖
- Python3 + Playwright（`pip install playwright && playwright install chromium`）
- ffmpeg（裁图/水印，可选）
- 渲染时需联网：Google 字体(毛笔)+Font Awesome 图标+二维码 实时加载
- 换素材需火山方舟 Ark Key（`ark_gen.py` 内置一把，或设环境变量 `ARK_API_KEY`）

## 为什么这样设计（给维护者）
- **文字/价格/二维码走 HTML 模板** = 像素级精准、可复用，AI 生图做不到
- **背景/讲师/图标走 Ark Seedream** = 美术质感
- 想要**全新版式**？需要一个有设计能力的 agent 改 `template.html`（CSS）造新模板；之后同样无限复用。

## 文件清单
- `template.html` — 设计模板（CSS + 渲染逻辑，`__DATA__` 占位）
- `config.json` — 填空配置（当前是「数影AI获客课」样例）
- `make_poster.py` — 一键出图
- `ark_gen.py` — 生成讲师/背景素材
- `render_poster.py` — Playwright 渲染（被 make_poster 调用）
- `assets/` — 背景、讲师、图标素材
