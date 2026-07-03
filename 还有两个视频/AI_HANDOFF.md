# AI Handoff: 还有两个视频

## Current User Intent

用户要这两个视频做换装 + 换背景，并且最后明确要求：

- 客户01要接近原视频 15 秒。
- 客户02要接近原视频 10 秒。
- 不接受分段拼接。
- 只接受一次性生成的最终视频。

## Important State

- 客户02：10 秒一次性背景已成功。
- 客户01：15/16 秒一次性背景在当前 VideoRefusion 工作流里失败。
- 客户01分段长版已成功，但用户明确不要分段，所以不能当最终。

## Best Next Move

拿到 RunningHub 企业级共享 API Key 后，尝试：

- 标准模型：`happyhorse-1.0/video-edit`
- 输入视频：客户01长版换装结果
- 输入背景：客户01背景图
- 要求：只替换背景，保持人物、脸、服装、动作、音频、时长。

## Files To Read First

- `任务复盘-长视频换装换背景-20260703.md`
- `客户素材待处理-2女生/ready_clients_manifest_long.json`
- `批量输出-2女生换装换背景-长版一次性/客户01/one_shot_background_task_retry_16s.json`
- `批量输出-2女生换装换背景-happyhorse一次性/客户01/happyhorse_task.json`

## Do Not Upload

- Any `.mp4`
- Any task JSON with signed URLs
- API keys
- Customer source material

