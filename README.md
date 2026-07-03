# seedance-tryon-video · 真人视频换装 & 换背景技能

这是一个 **Claude / Codex 技能仓库**：给真人短视频**换装**和/或**换背景**，保持原视频里的人脸、动作、镜头不变。生产走 RunningHub 两段式（换装 Wan2.2 Animate + 换背景 VideoRefusion），由脚本批量驱动。

## 给同事：怎么用

1. **拿到这个仓库后，让你的 AI 助手读 [`SKILL.md`](SKILL.md)** —— 完整、傻瓜化的操作步骤都在里面。
2. 第一次用：按 SKILL.md 第 1~3 步装依赖、配 API Key，然后用 [`references/示例素材/`](references/示例素材/README.md) 自带的样例（人物视频 + 衣服图 + 背景图）**先在本地跑通一遍**。
3. 跑通后再处理真实客户。

需要的素材（AI 会主动问你）：

| 素材 | 必须? |
|------|------|
| 换装视频（人物视频） | ✅ 必选 |
| 衣服图 | ⬜ 可选（给了才换装） |
| 背景图 | ⬜ 可选（给了才换背景） |

> RunningHub API Key 由团队负责人单独提供，配成环境变量 `RUNNINGHUB_API_KEY`，**不要提交到 Git**。

## 仓库结构

```
SKILL.md              技能主文档（AI 从这里开始）
requirements.txt      Python 依赖
scripts/              5 个驱动脚本（扫描 / 生成清单 / 运行换装换背景）
references/           速查、原理、边界、交接模板
  示例素材/            自带可试跑的样例（视频+衣服图+背景图）
docs/                 中文战斗经验 / 成功复盘 / 长视频复盘
agents/               agent 元信息
build_skill.sh        打包成 .skill 分发包
workspace/            本地项目工作区（客户素材/产出/实验，不进 Git）
```

## 打包分发

```bash
bash build_skill.sh   # 生成 dist/seedance-tryon-video.skill
```

## 安全

客户视频、成片、含签名 URL 的任务 JSON、`.env`、API Key **一律不进 Git**（`.gitignore` 已排除）。真实客户素材只留本地 `workspace/`。
