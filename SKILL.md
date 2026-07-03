---
name: seedance-tryon-video
description: 给真人短视频换装 / 换背景（Seedance 美业活动真人视频）。当用户想给一段人物视频替换衣服、替换背景，或两者都换，同时保持原视频里的人脸、动作、镜头不变时使用本技能。基于 RunningHub 两段式 AI App（换装 Wan2.2 Animate + 换背景 VideoRefusion），由脚本批量驱动。也适用于长视频时长处理、一次性 vs 分段换背景边界、质检、以及不上传客户素材/密钥的安全交付。Use for Seedance beauty-event try-on videos that replace clothing and/or background via RunningHub while keeping the original person, face, motion, and camera.
---

# Seedance 真人视频 · 换装 & 换背景

## 这个技能是干什么的

给一段**真人短视频**做两件事之一或两者：

- **换装**：保持视频里的人、脸、动作、镜头不变，只把身上的衣服换成一张「衣服参考图」里的款式。
- **换背景**：把视频背景换成一张指定「背景图」（花墙、门店、活动场景等）。

生产走 **RunningHub 两段式**，别追求"一步到位"：

1. **第 1 段 · 换装**：AI App `视频换装V2 Animate Wan2.2=B站艾橘溪`
2. **第 2 段 · 换背景**：AI App `【c0120】VideoRefusion 动态替换视频背景`

全流程由本仓库的 Python 脚本驱动。**AI 助手请严格按下面的步骤执行，不要跳步。**

---

## 第 0 步（最重要）：先向用户索要素材

在做任何生成之前，**必须先问用户要素材**。三样东西，只有第 1 样是必须的：

| # | 素材 | 是否必须 | 说明 |
|---|------|---------|------|
| 1 | **换装视频**（人物视频） | ✅ **必选** | 要处理的那段真人视频。竖版最佳（如 1080×1920）。 |
| 2 | **衣服图**（衣服参考图 / 参考视频） | ⬜ 可选 | 想换成的衣服。给了就换装；不给就不换装。图要干净：正面平铺或上身，别带手机截图 UI、黑边、杂乱背景。 |
| 3 | **背景图** | ⬜ 可选 | 想换成的背景。给了就换背景；不给就保留原背景。 |

**根据用户给了什么，自动决定做哪种模式：**

| 用户提供 | 模式 | 做什么 |
|---------|------|-------|
| 视频 + 衣服 + 背景 | `换装+换背景` | 先换装，再换背景（完整两段式） |
| 视频 + 衣服 | `只换装` | 只跑换装，换装结果就是成片 |
| 视频 + 背景 | `只换背景` | 跳过换装，原视频直接换背景 |
| 只有视频 | ❌ 无法处理 | 提醒用户：至少要给衣服图或背景图其中一样 |

> AI 助手：如果用户只发了视频，就主动问："您想换衣服、换背景，还是两者都换？请把对应的衣服图 / 背景图发我。" 不要默认三样都要，也不要因为缺衣服或缺背景就拒绝——缺哪个就跳过哪个阶段。

---

## 第 1 步：准备运行环境（同事第一次用时做一次）

需要 **Python 3.9+**，然后装两个依赖：

```bash
pip install runninghub-sdk opencv-python
# 或： pip install -r requirements.txt
```

- `runninghub-sdk`：调用 RunningHub API 的官方 SDK（脚本 `import runninghub_sdk`）。
- `opencv-python`：读视频的分辨率、帧率、时长（`import cv2`）。

## 第 2 步：配置 RunningHub API Key

脚本从环境变量 `RUNNINGHUB_API_KEY` 读取密钥（**绝不要把密钥写进代码或提交到 Git**）。密钥由团队负责人提供给你。

```bash
export RUNNINGHUB_API_KEY="你拿到的密钥"
```

想每次开终端都自动生效，可写进 `~/.zshrc` 或 `~/.bashrc`。验证：

```bash
echo $RUNNINGHUB_API_KEY   # 能打印出密钥即 OK
```

> 账户里要有 RunningHub 余额，否则生成会报 `[812] 企业版余额不足`。

---

## 第 3 步：先用自带样例跑通一遍（强烈建议）

本仓库 `references/示例素材/` 自带一套可直接跑的样例（人物视频 + 衣服图 + 背景图）。第一次用先拿它验证环境是否 OK，再处理真实客户。

详细一键跑通步骤见 **`references/示例素材/README.md`**。核心就是：把样例摆成客户目录结构 → 扫描 → 生成 manifest → 运行。

---

## 第 4 步：整理客户素材目录

每个客户一个目录，固定三件套子文件夹（**文件夹名必须完全一致**，脚本靠名字识别）：

```text
客户素材待处理/
  客户01/
    人物视频/            # 放换装视频（必须）
    衣服图或参考视频/     # 放衣服图（可选，不换装就留空/不建此文件夹）
    背景图/              # 放背景图（可选，不换背景就留空/不建此文件夹）
  客户02/
    ...
```

- 支持视频格式：`.mp4 .mov .m4v`；图片：`.jpg .jpeg .png .webp`
- 每个子文件夹里放**一个**主素材即可（有多个时脚本取排序第一个）。
- **不要覆盖用户原始文件**，复制进来。

## 第 5 步：扫描素材，确认齐全

```bash
python3 scripts/scan_tryon_clients.py --root "客户素材待处理"
```

输出会告诉你每个客户是 `READY [模式]` 还是 `MISSING ...`。例如：

```
客户01: READY [换装+换背景]
客户02: READY [只换装]
客户03: MISSING 衣服图或背景图（至少一项）
```

## 第 6 步：生成任务清单 manifest

**短测（统一 6 秒，先验证效果，便宜快）：**

```bash
python3 scripts/build_tryon_client_manifest.py \
  --root "客户素材待处理" \
  --out  "客户素材待处理/ready_clients_manifest.json" \
  --seconds 6 --width 576 --height 1024 --target Clothes
```

> 只想导出素材齐全的客户、跳过缺素材的，加 `--allow-partial`。

**成片（匹配每个视频的原始时长）：**

```bash
python3 scripts/build_duration_manifest.py \
  --root "客户素材待处理" \
  --out  "客户素材待处理/ready_clients_manifest_long.json" \
  --rounding ceil
```

> ⚠️ 别默认拿 6 秒当成片交付。用户要"原时长/一次性"时用 `build_duration_manifest.py`。长视频换背景有硬边界，见下方"长视频"一节。

## 第 7 步：运行生成

**主用（串行，最稳，样例和单客户都用它。已支持三种模式，会按 manifest 里有没有衣服/背景自动跳过对应阶段）：**

```bash
python3 scripts/run_tryon_bg_from_manifest.py \
  --manifest "客户素材待处理/ready_clients_manifest.json" \
  --out-dir  "批量输出" \
  --poll-interval 30 --timeout 9000
```

**多客户、且都要换装+换背景时可选（并行续跑，避免被慢任务卡死；只做完整两段式）：**

```bash
python3 scripts/run_tryon_bg_parallel_resume.py \
  --manifest "客户素材待处理/ready_clients_manifest.json" \
  --out-dir  "批量输出" \
  --poll-interval 30 --timeout 9000
```

输出结构：`批量输出/客户01/01_tryon_output/`（换装成片）、`02_background_output/`（换背景成片）、`batch_log.json`（任务记录）。

---

## 关键参数与稳定性经验（照做，能省很多坑）

- **`--target` 填 `Clothes`**，不要写"蓝白格纹荷叶边连衣裙"这类详细中文描述。详细提示词反而容易让模型保留原衣服、搞错领口/肩部结构。
- **尺寸推荐 `576 × 1024`** 生成，成片后再放大回原尺寸。
- **衣服参考图要干净**：别带手机 UI、"1/4"页码、黑边、杂乱背景。
- **换背景阶段很慢**，可能长时间卡在 `RUNNING`——**只有 `FAILED` 才算失败**，别看到 RUNNING 就重试。
- 换背景可能再次影响脸部和边缘，**成片后一定要质检**。

## 长视频 / 一次性换背景的边界（2026-07-03 实测）

- 换装（Wan2.2 Animate）：约 **10 秒、15 秒都成功**。
- 换背景（VideoRefusion）**一次性**：约 **10 秒成功**，**15/16 秒失败**。
- 想要长视频"一次性不分段"换背景，超过 ~10 秒目前不稳。分段换背景再拼接能出长片，但那**不是"一次性生成"**。
- `happyhorse-1.0/video-edit` 标准模型可能是长视频一次性方向，但 RunningHub 要求**企业共享 API Key**，普通 Key 会被拒。
- 详见 `references/long-video-boundaries.md` 与 `docs/任务复盘-长视频换装换背景-20260703.md`。

## 常见报错

| 报错 | 含义 | 处理 |
|------|------|------|
| `请先设置 RUNNINGHUB_API_KEY 环境变量` | 没配密钥 | 回到第 2 步 `export` |
| `[812] 企业版余额不足，请充值` | 账户没余额 | 找负责人充值 |
| `[421] TASK_QUEUE_MAXED` | 队列/并发满了 | 改用串行脚本，一次跑一个客户，稍后重试 |
| `Standard Model API is restricted to Enterprise-Shared API Keys only` | 当前 Key 调不了标准模型（如 happyhorse） | 需要企业共享 Key，普通 Key 不行 |

## 质检与交付

1. 确认成片存在、能本地播放、时长符合预期。
2. 做一张质检拼图（源视频 / 衣服 / 背景 / 成片对比）+ 一个 HTML 预览页给用户挑选。
3. 挑选后的成片放进交付目录。

## 🔒 安全红线（务必遵守）

- **绝不把客户视频、成片、含签名 URL 的任务 JSON、`.env`、API Key 上传到 GitHub。** 本仓库 `.gitignore` 已排除这些，但你新建目录时也要守住。
- API Key 只走环境变量 `RUNNINGHUB_API_KEY`，不硬编码进脚本。
- 客户真实素材只留本地（放 `workspace/` 等未跟踪目录），只有脚本、文档、技能自带样例进 Git。

---

## 参考文档索引

- `references/示例素材/README.md` —— **自带样例一键跑通步骤（新人从这里开始）**
- `references/runninghub-workflow.md` —— 两个 AI App 的 WebApp ID、节点、命令速查
- `references/工作流原理.md` —— 为什么两段式、每个模型（Wan2.2 Animate / VideoRefusion）怎么工作
- `references/long-video-boundaries.md` —— 长视频 / 一次性换背景边界
- `references/handoff-template.md` —— 给下一个 AI 的交接模板
- `docs/RunningHub视频换装换背景战斗经验.md` —— 完整踩坑记录
- `docs/视频换装换背景-成功经验-20260703.md` —— 4 女生批量成功复盘
- `docs/任务复盘-长视频换装换背景-20260703.md` —— 长视频实测复盘
