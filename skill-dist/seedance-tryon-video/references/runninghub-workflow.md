# RunningHub Workflow Reference

## Baseline

The most reproducible chain is not one-step generation. Use two stages:

1. Try-on: `视频换装V2 Animate Wan2.2=B站艾橘溪`
2. Background replacement: `VideoRefusion 动态替换视频背景`

## Try-On

WebApp ID: `1969605116187844610`

Nodes:

- `363.video`: person/source video
- `373.image`: clothing reference
- `362.value`: seconds
- `358.value`: width
- `359.value`: height
- `372.text`: target

Recommended settings:

- `width=576`
- `height=1024`
- `target=Clothes`

Use `Clothes`, not a long detailed clothing prompt. Detailed prompts often preserve the original clothing or distort neckline/shoulder structure.

## Background

WebApp ID: `1986353521488523266`

Nodes:

- `352.video`: try-on output video
- `318.image`: target background image
- `339.int`: seconds

This workflow can be slow and may stay `RUNNING` for many minutes. Only treat `FAILED` as failure.

## Scripts

Scan material directories:

```bash
python3 scripts/scan_tryon_clients.py --root "<root>"
```

Build a short-test manifest:

```bash
python3 scripts/build_tryon_client_manifest.py \
  --root "<root>" \
  --out "<root>/ready_clients_manifest.json" \
  --seconds 6 \
  --width 576 \
  --height 1024 \
  --target Clothes
```

Build an original-duration manifest:

```bash
python3 scripts/build_duration_manifest.py \
  --root "<root>" \
  --out "<root>/ready_clients_manifest_long.json" \
  --rounding ceil
```

Run serial:

```bash
RUNNINGHUB_API_KEY="$RUNNINGHUB_API_KEY" \
python3 scripts/run_tryon_bg_from_manifest.py \
  --manifest "<manifest>" \
  --out-dir "<output-dir>" \
  --poll-interval 30 \
  --timeout 9000
```

Run resumable:

```bash
RUNNINGHUB_API_KEY="$RUNNINGHUB_API_KEY" \
python3 scripts/run_tryon_bg_parallel_resume.py \
  --manifest "<manifest>" \
  --out-dir "<output-dir>" \
  --poll-interval 30 \
  --timeout 9000
```

If `TASK_QUEUE_MAXED` appears, switch to serial/single-client execution.

