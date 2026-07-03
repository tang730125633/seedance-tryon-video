# Long Video and One-Shot Background Boundaries

## Case Study: "还有两个视频" 2026-07-03

Source videos:

- Customer 01: about 15.03s, 1080x1920, 30fps
- Customer 02: about 9.53s, 1080x1920, 30fps

## Results

Short-test run:

- Both customers succeeded at about 5.96s.
- This was not acceptable because the user expected original duration.

Long try-on:

- Customer 01 try-on succeeded; output was about 16.03s.
- Customer 02 try-on succeeded; output was about 10s.

VideoRefusion one-shot background:

- Customer 02 about 10s one-shot background succeeded.
- Customer 01 about 15s failed.
- Customer 01 about 16s retry also failed.

Chunked background:

- Customer 01 succeeded when background was run in short chunks and concatenated.
- Customer 02 also succeeded with chunks.
- This satisfies duration but does not satisfy "一次性生成".

Happyhorse attempt:

- Candidate model: `happyhorse-1.0/video-edit`
- Ordinary API key was rejected:

```text
Access Denied: Standard Model API is restricted to Enterprise-Shared API Keys only.
```

## Decision Rules

If the user asks for original duration:

- Do not deliver a default `seconds=6` result.
- Infer or inspect source durations and set per-client seconds.

If the user asks for one-shot generation:

- Do not deliver chunked results as final.
- VideoRefusion can be tried around 10s.
- For 15s one-shot, expect VideoRefusion failure and use a long-video-capable workflow or RunningHub standard model with Enterprise-Shared API Key.

If the user accepts "duration-correct but not one-shot":

- Chunking plus concatenation is a practical fallback.
- Clearly label it as chunked, not one-shot.

## Prompt For One-Shot Video Edit

```text
Replace only the background of the video with the provided beauty-event background image.
Keep the same adult woman, same face identity, same clothing, same skincare motion,
same framing, same timing, and original audio. Do not change the person or clothing.
Only replace the room background.
```

