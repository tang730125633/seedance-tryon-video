# Seedance 真人视频 · 美业活动项目

> 目标：用**真实授权模特照片**（Tang + 同事）做**图生视频(i2v)**，验证两个门槛——
> ① 成本远低于 1元/秒　② 突破以往 API 对真人形象生成的限制。

## 素材
- `refs/person_A_zelong.jpg` — Tang（白T，已转正 1600px）
- `refs/person_B_colleague.jpg` — 同事（黑T眼镜，已转正 1600px）
- 授权：本人及同事，仅内部测试用。

## 中转站：api.zdc.mom（new-api 灰色聚合站）
- key 见 `secret.env`（本地 600，不进 git）
- 计费：**按次**（非按秒）→ seedance-2-0 `0.85/条`、seedance-2-0-fast `0.75/条`、grok-imagine-video `0.4/条`、gpt-image-2 `0.1/张`
- 视频端点：`POST /v1/videos`（Sora 风格，`seconds` 必须是**字符串**）

## 测试记录（2026-06-17）
| 模型 | 结果 |
|---|---|
| gpt-5.5 文本 | ✅ 200，key 有效有余额 |
| gpt-image-2 生图 | ✅ 200 出图，GPT 分组可访问 |
| seedance-2-0（JSON）| ❌ `get_channel_failed: 分组 auto 下模型 seedance-2-0 的可用渠道不存在` |
| seedance-2-0（Sora multipart）| ❌ 同上（**非格式问题**）|
| grok-imagine-video | ❌ 同上（所有视频模型都无渠道）|
| 凭据 4eda83d1...（raw/sk-）| ❌ Invalid token |

### 结论
- key/余额/分组/格式都没问题；**是该站 seedance/grok 视频上游渠道为空，当前调不出视频**。
- 图片通道（gpt-image-2）是活的 → 可先在此站验证**真人图生图/改图**。

## ⭐ 最终结论（2026-06-17）：用火山 Ark，不用灰站

**两个门槛都在火山 Ark 官方通道上解决了：**

| 维度 | 灰站 zdc.mom (Seedance 2.0) | **火山 Ark (Seedance 1.0 pro i2v)** ✅ |
|---|---|---|
| 真人还原 | ❌ **参考图被丢弃**，出陌生人 | ✅ **完美保住真人脸**（首帧=参考照）|
| 速度 | ❌ 10+ 分钟、撞 17 次才创建成功 | ✅ **45 秒、一次成功** |
| 成本 | 按次 ~¥6/条 | ✅ 720p ≈¥1.3/条(4s)，lite-i2v 可降到 ~¥0.9 |
| 通道 | 灰色不稳、随时跑路 | ✅ 官方直连、国内备案 |

**灰站致命伤**：它**不转发 `input_reference` 参考图**（`multipart: NextPart: EOF`），
所以无论文生还是"图生"，上游都只收到文字 → 永远出陌生人。Seedance 2.0 再强也没用。

**正解脚本**：`scripts/ark_i2v.py <参考图> "<英文prompt>" <输出> [dur] [resolution] [ratio]`
- 引擎：火山 Ark `doubao-seedance-1-0-pro-250528`，`content` 里塞 `image_url`(base64) 当首帧
- 成片样例：`output/04_person_B_ark_i2v.mp4`（同事真人、自然微笑、832×1120 竖版 4s）

## 产物
- `output/01_text_salon.mp4` — 灰站文生样片（证明灰站能出片但忽略图）
- `output/02_person_B_i2v.mp4` — 灰站"i2v"=陌生女人（**反面教材：参考图被丢**）
- `output/04_person_B_ark_i2v.mp4` — ✅ **火山 Ark 真人 i2v，同事本人动起来**

## 待办
- [ ] 试 lite-i2v 模型(`doubao-seedance-1-0-lite-i2v-250428`)进一步降本
- [ ] person_A(Tang) 也跑一条；试美业场景 prompt（前后对比/产品展示/口播）
- [ ] 把 ark_i2v 能力并进 video-maker bot（飞书 @ 即可出真人视频）
