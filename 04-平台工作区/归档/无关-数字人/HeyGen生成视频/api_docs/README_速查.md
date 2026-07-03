# HeyGen CLI/API 速查表（泽龙真人口播用）

> 目的：照着填、不瞎猜。完整字段见同目录 `schema_*.json`，命令帮助见 `cli_*.txt`。

## 0. 前提
- CLI：`~/.local/bin/heygen`（v0.1.5，官方）
- 登录：key 已存 `~/.heygen/credentials`（`heygen auth login`）
- **代理（必须）**：HeyGen 是美国的，国内要走代理。每条命令前加：
  ```bash
  export PATH="$HOME/.local/bin:$PATH"
  export HTTPS_PROXY=http://127.0.0.1:1082 HTTP_PROXY=http://127.0.0.1:1082
  ```
- **计费**：API 钱包（wallet，独立于网页VIP）。标准 ~$1/分钟（30秒≈$0.5），Avatar IV $4/分钟（30秒≈$2）。额度12个月有效。查余额：`heygen user me get`

## 1. 核心工作流（照片→真人口播）
```
① 上传照片     heygen asset upload  → 拿 asset_id / url
② 生成视频     heygen video create -d '{...}' --wait  → 拿 video_id
③ 查/下载     heygen video get / heygen video download
```

## 2. `video create` 关键字段（type=image 分支 = 我们用的）
用 `-d '{JSON}'`。字段：
| 字段 | 说明 |
|---|---|
| `type` | `"image"`（照片口播）|
| `image` | 照片：`{"type":"url","url":"..."}` 或 `{"type":"asset","asset_id":"..."}` |
| `script` | 要念的文案（HeyGen TTS 读）—— 与 audio 二选一 |
| `audio_url` / `audio_asset_id` | **喂我们自己的克隆音频**做对口型（与 script 二选一）⭐ |
| `voice_id` | 用 script 时选声音；可 `heygen voice list` 找中文男声 |
| `voice_settings` | 语速/情绪等 |
| `motion_prompt` | ⭐**肢体语言提示**（双手抱胸/玩手指/前倾等，就放这里）|
| `caption` | 字幕开关/样式 |
| `engine` | 引擎：Avatar IV(最真,$4/min) / Avatar V |
| `expressiveness` | 表现力强度 |
| `aspect_ratio` | 如 `"9:16"`（竖屏）|
| `resolution` | 如 `"1080p"` |
| `background` / `remove_background` | 背景 |
| `output_format` | 输出格式 |
| `title` | 视频标题 |

> 另两个分支：`type=avatar`（用HeyGen现成形象+engine）；`type` 第三支是 prompt→video（agent式，字段 prompt/references/duration）。

## 3. 命令模板（拿到 asset_id 后）
```bash
# A. 用克隆音频对口型（推荐：你的声音）
heygen video create -d '{
  "type":"image",
  "image":{"type":"asset","asset_id":"<照片asset_id>"},
  "audio_url":"<克隆音mp3的可访问URL>",
  "motion_prompt":"对着镜头自然轻松说话，双手交叉放膝盖偶尔玩手指，说到重点身体微前倾，自然眨眼挑眉，不要僵硬",
  "caption":true,
  "engine":"avatar_iv",
  "aspect_ratio":"9:16",
  "resolution":"1080p",
  "title":"泽龙口播测试"
}' --wait

# B. 用HeyGen配音念脚本（最快）
heygen video create -d '{
  "type":"image",
  "image":{"type":"asset","asset_id":"<照片asset_id>"},
  "script":"你的文案...",
  "voice_id":"<中文男声voice_id>",
  "motion_prompt":"...肢体语言...",
  "caption":true,"engine":"avatar_iv","aspect_ratio":"9:16","resolution":"1080p"
}' --wait
```

## 4. 待确认（生成时实测）
- `engine` 的确切取值（avatar_iv / avatar_v 的准确字符串）→ 看 `schema_video_create.json`
- `audio_url` 需公网可访问；本地克隆音可能要先上传成 asset 或放图床
- 中文 `voice_id` → `heygen voice list --human | grep -i chinese`
- 字幕 `caption` 的中文支持/样式

## 文件清单
- `schema_video_create.json` — 视频生成完整字段（27KB，权威）
- `schema_avatar_create.json` / `schema_lipsync_create.json` / `schema_voice_create.json`
- `cli_*.txt` — 各命令 --help
- `00_heygen_help.txt` — 顶层命令

---

# 🔥 实战记录（边做边记，避免重复踩坑）

## 2026-06-20 首条成功

### ✅ 跑通的最小命令（type=image + 克隆音对口型）
```bash
export PATH="$HOME/.local/bin:$PATH"
export HTTPS_PROXY=http://127.0.0.1:1082 HTTP_PROXY=http://127.0.0.1:1082
# ① 上传照片 → 拿 asset_id
heygen asset create --file "zelong_真人照/3930xxx.jpg"   # 返回 data.id
# ② 上传克隆音 → 拿 audio asset_id
heygen asset create --file "output_voice/克隆测试01.mp3"  # 返回 data.id
# ③ 生成（注意JSON结构）
heygen video create -d '{
  "type":"image",
  "image":{"type":"asset_id","asset_id":"<照片id>"},
  "audio_asset_id":"<音频id>",
  "motion_prompt":"对着镜头自然轻松说话，偶尔点头眨眼，说到重点身体微前倾，不要僵硬",
  "aspect_ratio":"9:16",
  "resolution":"720p",
  "title":"标题"
}'   # 返回 data.video_id
# ④ 查状态 / 下载
heygen video get -d '{"video_id":"<id>"}'
heygen video download ...
```

### ⚠️ 已踩的坑
1. **`engine` 字段 image 类型不能加！** 报 `Extra inputs are not permitted`。engine（`{"type":"avatar_iv"}`）只用于 `type=avatar` 分支。**照片(type=image)默认就是 Avatar IV，不要传 engine**。
2. **zsh 不拆分变量**：`heygen $cmd` 会把 "video create" 当一个参数→报 unknown command。要显式写或用 bash 拆分。
3. **必须走代理**：不加 `HTTPS_PROXY=http://127.0.0.1:1082` 连不上（HeyGen美国服务器）。posthog 分析超时是正常的（它连美国分析服务器），不影响主请求。
4. **asset 上传**：`heygen asset create --file <路径>`，max 32MB，支持 png/jpeg/mp4/mp3/wav/pdf，返回 `data.id`。
5. **image 写法**：`{"type":"asset_id","asset_id":"..."}`（type 跟字段名一致）；也可 `{"type":"url","url":"..."}`。
6. **克隆音对口型**：用 `audio_asset_id`（先把mp3传成asset）或 `audio_url`（公网URL）。与 script+voice_id 互斥。

### 待验证
- `caption` 字段的中文字幕效果（schema说是 sidecar 字幕文件，可能不烧进画面，要后期ffmpeg烧）
- `motion_prompt` 实际对肢体语言的控制力多强
- 720p vs 1080p 画质 / Avatar IV 的实际计费
7. **`video get` 是位置参数**：`heygen video get <video-id>`（不是 -d JSON！用 -d 会返回空）。
8. **asset 上传(图片+音频)统一返回 `data.asset_id`（不是 data.id！）。视频生成返回 data.video_id**。
9. **HeyGen不收m4a**，音频先转 mp3/wav 再传。声音克隆=`voice clone create --voice-name X -d {audio:{type:asset_id,asset_id:..}}`→ voice_clone_id，轮询到status=complete可用。
10. **`expressiveness` 默认 low！** 取值 high/medium/low，做表现力强的口播必须设 high（大鹏反馈"太平"的关键原因）。
