# 🎬 数字人口播 · 完整流程解决方案（一条龙 SOP）

> 从「一张照片 + 一段素材」到「成片」的全部方案与命令。配合 `00_数字人总索引_README.md`(导航) + `技术方案_定制化真人口播.md`(旋钮表) 使用。
> 基目录：`~/Desktop/Seedance真人视频-美业活动/` ｜ 凭证：`_凭证总表_KEEP_SAFE.env`

---

## 0. 总流程图
```
                 ┌─ 音频从哪来？(三选一) ─┐
照片(正脸)        │ A 本人真录音/原视频 → 数字复刻(最像)        │
  │修EXIF/裁剪     │ B 克隆声+新文案 → 火山/IndexTTS2/ElevenLabs │ → 音频.wav/mp3
  ▼               │ C 不克隆,HeyGen自带中文声念文案(最快)       │      │
上传HeyGen ◄───────└──────────────────────────────────────────┘      │
  │                                                                    ▼
  └──────────► HeyGen Avatar IV 对口型(expressiveness匹配情绪) ──► 成片.mp4
                                                                       │
                                                  (可选)后期烧大黄字+滚动字幕
```

**铁律**：声音情绪强度 ↔ HeyGen `expressiveness` 必须匹配（都high或都medium），否则违和。

---

## 1. 准备照片（底图）
- **优先用真实场景截图**（原视频帧/工作照）> 影楼摆拍，背景眼神更可信。
- 从视频抽帧：`ffmpeg -ss 30 -i 视频.mp4 -frames:v 1 -q:v 2 帧.jpg`，挑**正脸、嘴自然、没字幕遮挡**的。
- 裁掉底部字幕条/裁上半身（全身照脸太小）：PIL crop。`make_koubo.py` 会自动修EXIF方向。
- 要求：清晰正脸、看镜头、光线好。侧脸/全身/张嘴抓拍 → HeyGen会animate得别扭。

## 2. 准备音频（三条方案）

### 方案A · 数字复刻（最高保真，有本人原声时首选）
直接用本人真录音/原视频音频，HeyGen只对口型。
```bash
# 从原视频抽高音质音频
ffmpeg -i 原视频.mp4 -vn -ar 44100 -ac 1 -b:a 192k 原声.mp3
```
→ 直接进第3步喂 HeyGen。**零违和**（声音=本人）。局限：只能复刻已录过的内容。

### 方案B · 克隆声 + 任意新文案（可批量、可换人）
三个引擎任选：

| 引擎 | GPU? | 情绪 | 命令/脚本 |
|---|---|---|---|
| **火山豆包复刻** | 否(云端) | 中 | `scripts/hs_tts.py`（speaker S_EdeJFdm62 已训） |
| **IndexTTS2** | 是(GPU) | 强(emo_vector) | GPU上 `gen_emotion.py` |
| **ElevenLabs v3** | 否(云端) | 最强(音频标签) | `scripts/eleven_tts.py`（待key） |

**IndexTTS2 情绪声**（GPU开机后）：
```bash
set -a; source ~/.autodl/instance.env; set +a   # 先开机:AutoDL控制台
# 上传参考音(克隆谁的嗓子) + 跑
.venv/bin/python gen_emotion.py --ref 参考音.wav --text "文案" \
   --emovec "0.45,0.2,0,0,0,0,0.35,0" --alpha 0.8 --out out.wav   # 激情
# 平和: 用 --emo "自信平稳真诚" --alpha 0.4 (注:emo_text会被判calm,要真激情用emovec)
```
**ElevenLabs**（拿到key后）：
```bash
python3 scripts/eleven_tts.py --list                       # 选中文voice_id
python3 scripts/eleven_tts.py --text "[激动]文案..." --voice <id> --model eleven_v3 --out out.mp3
```

### 方案C · HeyGen自带中文声念文案（最快，不克隆）
跳过克隆，直接让HeyGen念。中文男声 **Paul-Excited** `9aa98f478ac94b3a85272470dff2aae4`（⚠️BOB是女声别用）。
→ 第3步用 `--voice + --script` 而非 `--audio`。

## 3. HeyGen 对口型生成成片（统一入口）
```bash
# 喂音频(方案A/B)
python3 scripts/make_koubo.py --photo 正脸图.jpg --audio 音频.wav \
   --motion "肢体语言:怼脸激情/招商手势/双手抱胸…" \
   --expressiveness high --resolution 1080p --ratio 9:16 --out 成片.mp4
# 或HeyGen配音(方案C): 把 --audio 换成 --voice <id> --script "文案"
```
- 必须开 Mac 代理 `127.0.0.1:1082`（脚本已内置）。
- `expressiveness`：激情声配high，平和声配medium。
- 输出竖屏 9:16 给抖音。

## 4.（可选）后期字幕 — 让它=参考片那个味儿
> 待建脚本。两层：① 开头**大号黄字钩子**（"距离美业大洗牌仅剩10天"）② 全程**底部滚动字幕**。
> 方案：whisper转字幕 → ffmpeg drawtext烧大黄字 + subtitles烧滚动字幕；或用剪映。

---

## 5. 情绪调节 SOP
- **找人物专属甜点 alpha**：同一文案跑 纯克隆/0.4/0.55/0.8 几版，耳朵选最自然不失真的。大鹏≈0.4-0.55。
- **emo_vector 8维**：`[happy,angry,sad,afraid,disgusted,melancholic,surprised,calm]`
  - 激情揭露：`0.45,0.2,0,0,0,0,0.35,0`
  - 亲切沉稳：偏 calm，低 alpha
- **违和自查**：声音很激动但脸很平 = expressiveness设低了 → 调high。

## 6. 常见坑（直接查）
| 现象 | 原因/解法 |
|---|---|
| HeyGen连不上 | 没开代理1082 |
| 出来是女声 | 用了BOB,换Paul-Excited |
| 声音激情脸平静(违和) | expressiveness没设high |
| 情绪加了还是平 | emo_text被判calm,改用--emovec |
| 脸歪/侧 | 照片EXIF方向 or 用了侧脸图 |
| GPU开不了机 | 上次关机释放了,等GPU空闲或换卡型 |
| 视频是m4a音频 | 先转mp3再传 |

## 7. 成本对照（一条30-60秒口播）
| 环节 | 成本 |
|---|---|
| HeyGen对口型 | ~$0.2-0.6/条 |
| IndexTTS2(GPU) | ¥2.78/小时(开机期间),生成本身免费 |
| 火山复刻 | 极低/基本免费 |
| ElevenLabs | 约几分钱-几毛/条(credits) |

---

## 8. 三种方案怎么选（速查）
- **要最像本人、内容已录过** → 方案A 数字复刻
- **要换新文案/批量/给多人做** → 方案B 克隆声（中文母语感:火山>ElevenLabs;情绪表现力:ElevenLabs/IndexTTS2>火山）
- **只是快速出片、不在乎是不是本人声** → 方案C HeyGen自带声
