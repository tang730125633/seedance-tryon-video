---
name: seedance-tryon-video
description: Use this skill for Seedance beauty-event真人视频 workflows that replace clothing and backgrounds with RunningHub. It covers client material triage, manifest generation, RunningHub try-on and background AI Apps, long-video duration handling, one-shot versus chunked background constraints, QA contact sheets, and safe GitHub handoff without uploading customer media or API keys.
---

# Seedance Try-On Video

## Overview

Use this skill when the task is to produce, debug, document, or hand off the Seedance真人视频美业活动 workflow: keep the original person, face, pose, timing, and camera as stable as possible while changing clothing and/or background.

The current production baseline is RunningHub two-stage generation:

1. Try-on with `视频换装V2 Animate Wan2.2=B站艾橘溪`.
2. Background replacement with `VideoRefusion 动态替换视频背景`.

Read `references/runninghub-workflow.md` before executing production. Read `references/long-video-boundaries.md` when videos are longer than 6 seconds or the user says "一次性生成". Read `references/handoff-template.md` when preparing notes for another AI. Read `references/工作流原理.md` to understand why the pipeline is two-stage and how each model (Wan2.2 Animate try-on, VideoRefusion background) works.

## Critical Rules

- Confirm file roles before running cloud tasks: source person video, clothing reference, background image.
- Do not treat multiple user-provided videos as clothing references unless the user explicitly says so.
- Do not use default `seconds=6` for final delivery when the source is longer and the user expects original duration.
- If the user asks for "一次性生成", do not deliver a chunked/stitched result as final.
- Never upload customer videos, generated final videos, task JSON with signed URLs, `.env`, or API keys to GitHub.
- RunningHub API keys must come from `RUNNINGHUB_API_KEY`; do not hard-code keys in scripts.

## Standard Client Folder Structure

Each client must have a three-part directory:

```text
客户01/
  人物视频/
  衣服图或参考视频/
  背景图/
客户02/
  人物视频/
  衣服图或参考视频/
  背景图/
```

Use `scripts/scan_tryon_clients.py` to verify readiness:

```bash
python3 scripts/scan_tryon_clients.py --root "<客户素材目录>"
```

Use `scripts/build_tryon_client_manifest.py` for short tests, or `scripts/build_duration_manifest.py` for original-duration work.

## Production Defaults

Try-on AI App:

- WebApp ID: `1969605116187844610`
- Node `363.video`: source video
- Node `373.image`: clothing reference
- Node `362.value`: duration seconds
- Node `358.value`: width
- Node `359.value`: height
- Node `372.text`: target
- Recommended target: `Clothes`
- Recommended dimensions: `576 x 1024`

Background AI App:

- WebApp ID: `1986353521488523266`
- Node `352.video`: try-on video
- Node `318.image`: background image
- Node `339.int`: duration seconds

## Workflow

1. **Inventory**
   - List files in the user-specified folder.
   - Use `cv2` or another local tool to inspect dimensions, fps, and duration.
   - Generate a source-video contact sheet before cloud submission.

2. **Prepare material directories**
   - Copy source videos into `客户XX/人物视频/`.
   - Copy clothing references into `客户XX/衣服图或参考视频/`.
   - Copy background images into `客户XX/背景图/`.
   - Do not overwrite user originals.

3. **Build manifest**
   - For short tests: global `--seconds 6` is acceptable.
   - For final long videos: use `scripts/build_duration_manifest.py` with per-client seconds derived from source duration.

4. **Run RunningHub**
   - Use `scripts/run_tryon_bg_from_manifest.py` for serial runs.
   - Use `scripts/run_tryon_bg_parallel_resume.py` when queue behavior is stable and multiple tasks can run.
   - If RunningHub returns `TASK_QUEUE_MAXED`, run one client at a time.
   - If RunningHub returns enterprise balance or API-key errors, stop and report the exact blocker.

5. **QA**
   - Verify output exists, opens locally, and has expected duration.
   - Build a contact sheet with: source video, clothing reference, background, final output.
   - Create an HTML preview for the user.

6. **Document**
   - Record successful task paths and failed boundaries.
   - If results will be sent to another AI, create an `AI_HANDOFF.md`.
   - Push only safe docs/scripts to GitHub.

## Long Video and One-Shot Rules

The 2026-07-03 "还有两个视频" run established these boundaries:

- 6-second short tests can succeed but are not acceptable for original-duration delivery.
- Try-on succeeded at about 15 seconds and 10 seconds.
- VideoRefusion one-shot background succeeded at about 10 seconds.
- VideoRefusion one-shot background failed at about 15/16 seconds.
- Chunked background replacement can produce long-duration outputs but is not "一次性生成".
- `happyhorse-1.0/video-edit` may be the correct one-shot long-video direction, but RunningHub requires an Enterprise-Shared API Key.

See `references/long-video-boundaries.md` for details.

## Common Failure Messages

- `[812] 企业版余额不足，请充值`: API/enterprise balance is unavailable for the current key.
- `[421] TASK_QUEUE_MAXED`: queue/concurrency is full; retry later or run one client at a time.
- `Standard Model API is restricted to Enterprise-Shared API Keys only`: current key cannot call RunningHub standard model APIs such as happyhorse.

## Deliverable Checklist

- Source contact sheet exists.
- Final preview HTML exists.
- Final videos match requested duration expectations.
- QA contact sheet exists.
- README or handoff note explains whether the final is one-shot or chunked.
- No secrets, signed URLs, task JSON, or media files are committed to GitHub.

