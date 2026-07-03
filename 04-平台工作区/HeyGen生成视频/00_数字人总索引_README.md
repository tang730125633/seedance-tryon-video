# 🎬 数字人总索引（口播工厂导航）

> **这是我们数字人/真人口播全套训练数据与系统的总入口。** 以后找任何东西先看这里。
> 最后更新：2026-06-20 ｜ 维护：Claude Code 小秋
> 基目录（下文相对路径都从这里起）：`~/Desktop/Seedance真人视频-美业活动/`
> ⚠️ 真实密钥值**不写进本文档**（防泄漏），只给存放路径；要看值直接打开对应 `secret.*.env`（本地 600 权限，**别推 git/发群**）。

---

## 1️⃣ 密钥凭证（存放位置，不抄值）

| 用途 | 文件路径 | 里面有啥 |
|---|---|---|
| **HeyGen API** | `~/.heygen/credentials` | HeyGen API key（`heygen auth login` 写入）。API钱包独立于网页VIP |
| **云端GPU SSH** | `~/.autodl/instance.env` | 当前GPU实例 HOST/PORT/USER/PASS（5090，会随换机更新） |
| **火山声音复刻** | `secret.huoshan_tts.env` | HS_APPID=7856997538 / HS_ACCESS_TOKEN / HS_SPEAKER_ID=S_EdeJFdm62 |
| **XiaoLe中转**(出图/whisper不支持) | `secret.xiaole.env` | XIAOLE_KEY（gpt-image-2出图、GPT-5.4多模态） |
| **泽龙中转站** | `secret.zelong.env` | ZURL=api.zelong.vip / ZKEY |
| **OpenAI官方** | `secret.openai.env` | OPENAI_API_KEY（国内服务器连不通，备用） |
| 其它 | `secret.env` | 杂项 |
| 语音大模型凭证 | （Tang口头给过 `2ffff…`，火山系） | 见 AI-Memory log |

---

## 2️⃣ 连接 HeyGen CLI

- **CLI**：`~/.local/bin/heygen`（v0.1.5 官方）
- **必须走代理**（HeyGen美国服务器）：`export HTTPS_PROXY=http://127.0.0.1:1082 HTTP_PROXY=http://127.0.0.1:1082`
- **一键出片脚本**：`scripts/make_koubo.py`（自动修EXIF+上传+生成+轮询+下载）
  ```bash
  # 喂任意音频对口型（万能配方，推荐）
  python3 scripts/make_koubo.py --photo 正脸图.jpg --audio 任意音频.wav \
      --motion "肢体语言..." --expressiveness high --resolution 1080p --ratio 9:16 \
      --out 输出.mp4
  # 或用HeyGen配音念文案
  python3 scripts/make_koubo.py --photo 图.jpg --voice <voice_id> --script "文案" ...
  ```
- **速查表/踩坑**：`HeyGen生成视频/api_docs/README_速查.md`（10条坑：engine字段、asset_id、m4a转mp3、EXIF、代理、expressiveness默认low…）
- **HeyGen voice_id 速查**：
  - 大鹏老师克隆声：`b859c12ff2964feeb818e5fdd802d417`(55秒版,推荐) / `b9fff092d63746eeb201ff8fcaffbc4a`(13秒版)
  - HeyGen中文男声 **Paul-Excited**：`9aa98f478ac94b3a85272470dff2aae4`（招商激情，武俊杰5条用的）
  - ⛔ `BOB`(`dMkR1XwIkarpNqWUJLnX`)：gender=unknown **实际是女声，别用**
  - 找声音：`heygen voice list --language Chinese --gender male --engine starfish --limit 40`

---

## 3️⃣ 连接云端 GPU（IndexTTS2 情绪声）

- **平台**：AutoDL 控制台 https://www.autodl.com/console/instance/list （账号 炼丹师0982）
- **当前实例**：RTX 5090（A52机），SSH 见 `~/.autodl/instance.env`
- **连接方式**（绕国内代理 fake-ip 坑）：
  ```bash
  set -a; source ~/.autodl/instance.env; set +a
  env -u HTTPS_PROXY -u HTTP_PROXY sshpass -p "$PASS" ssh -o PreferredAuthentications=password \
      -o PubkeyAuthentication=no -p "$PORT" root@"$HOST"
  ```
- **IndexTTS2 目录**：`/root/autodl-tmp/work/index-tts/`（.venv torch2.8+cu128 / checkpoints 12G / `gen_emotion.py` 情绪生成脚本）
- **数据保命**：克隆实例可把数据盘迁到新机（不用重装）；**关机会释放GPU→可能抢不回**（上次的坑）。短期不用才关。
- 详细维修经验：AI-Memory `reference-openclaw-ssrf-fakeip` + log.md。

---

## 4️⃣ 训练数据沉淀（资产库）

### 🎙️ 声音素材（参考音/克隆源）
| 人 | 参考音 | 备注 |
|---|---|---|
| 泽龙 | `output_voice/口播01_躺床大哥风.mp3` 等 | 火山合成,可当IndexTTS2参考 |
| 火山泽龙音色 | speaker `S_EdeJFdm62` | 控制台自训,已成功 |
| 大鹏 | `大鹏老师/三向东路 5.m4a`(55s) | IndexTTS2参考音=GPU上 dapeng_ref.wav |

### 🖼️ 人物照片（HeyGen底图）
- `大鹏老师/大鹏_正脸_fixed.jpg`、`大鹏_原视频截图_怼脸.jpg`(原视频t30帧,最原生)、`照片库/`、`IMG_2131~2137.HEIC`
- `人物参考图/`（9张同事：武俊杰西装/正脸小哥/白T小哥/女同事/大鹏抓拍等）+ `武俊杰_上半身_fixed.jpg`(裁好的)
- `zelong_真人照/`（泽龙本人）

### 🎬 成片（口播视频）
- **大鹏「医美新规大洗牌」复刻**：`大鹏老师/大鹏_医美洗牌_原声数字复刻.mp4`(本人真声,109s,标杆) / `_完整版复刻.mp4`(合成激情声,92s) / `_钩子复刻.mp4` / `_原图复刻.mp4`
- **大鹏招商口播**：`大鹏老师/大鹏_甜点版口播_v5.mp4`(推荐) / `_自然版口播_v4.mp4` / `_情绪声口播_v1.mp4`
- **武俊杰东晟时代5条招商**：`人物测试/武俊杰_①痛点型_男声.mp4`～`⑤灵魂拷问型.mp4`
- **泽龙**：`API测试_泽龙口播01.mp4`

### 📝 文案库
- `口播文案库_大鹏_医美新规大洗牌.md`（三大杀招全文+大黄字钩子建议）
- `口播文案库_武俊杰_东晟时代.md`（5角度：痛点/反转/算账/真实反馈/灵魂拷问）

---

## 5️⃣ 情绪参数与语料调节

> 详细旋钮表 + 数据流见 **`技术方案_定制化真人口播.md`**（核心文档，先看它）

### IndexTTS2 情绪（GPU `gen_emotion.py`）
- ⚠️ **`emo_text` 中文描述会被判成 calm！** 真激情必须用 `--emovec` 喂8维向量：
  `[happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]`
- **激情揭露感参考**：`--emovec "0.45,0.2,0,0,0,0,0.35,0" --alpha 0.8`
- **alpha 甜点值**（情绪强度）：大鹏 ≈ **0.4~0.55**；泽龙待定（5条对照 `泽龙音色对照/` 待选）
- 命令：`.venv/bin/python gen_emotion.py --ref 参考音.wav --text "文案" --emovec "..." --alpha 0.x --out 输出.wav`（或 `--emo "文字描述"` 走平和）

### HeyGen 表情/肢体
- `expressiveness`：high / medium / low（**默认low=太平!**）
- **铁律：声音情绪 ↔ 脸expressiveness 必须匹配**（都high或都medium），错位=违和（v1哭腔教训）
- `motion_prompt`：自然语言描述肢体（怼脸激情/招商手势/双手抱胸…）

### 泽龙音色对照（待Tang定专属alpha）
`泽龙音色对照/` 下5条：成长S1×(纯克隆/自然0.4/甜点0.55) + 业务S2×(纯克隆/自然0.45)

---

## 📌 待办（接着干）
1. 大黄字钩子 + 滚动字幕**后期烧录脚本**（让成片=参考片那个味儿）
2. 武俊杰真录音 → 克隆他本人声音（替换HeyGen Paul声）
3. 泽龙专属 alpha 定稿（听5条对照选一版）
4. GPU 用完关机（注意会释放）
