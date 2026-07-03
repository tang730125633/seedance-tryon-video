#!/usr/bin/env python3
"""Try Veo 3.1 with the original video as a motion/identity reference.

This is an experiment: if the Gemini API rejects this request, Veo cannot be
used for strict source-video editing through this endpoint.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from google import genai
from google.genai import types


ROOT = Path("/Users/xlzj/Desktop/Seedance真人视频-美业活动")
SOURCE_VIDEO = ROOT / "测试111换装测试/f2ebeb6f78e789aff274edc48391b8f9.mp4"
CLOTHES = ROOT / "测试111换装测试/图三.jpg"
BACKGROUND = ROOT / "测试111换装测试/图二.jpg"
OUT_DIR = ROOT / "02-生成产出/output_veo31_video_reference_strict"

MODEL = os.environ.get("VEO_MODEL", "veo-3.1-fast-generate-preview")

PROMPT = """Use the provided video as the exact motion and identity reference.
Do not make the woman talk. Do not animate speech. Keep her mouth naturally closed except for the original subtle expression.
Keep the same adult woman, same face identity, same facial proportions, same skin texture, same hairstyle, same pearl earrings, same necklace, same facial skincare patches, same head movement, same hand movement, same timing, same selfie camera framing, and same overall motion from the original video.
Only change two things:
1. Replace the purple outfit with the referenced blue and white gingham ruffle outfit with white bow, front buttons, and white layered skirt details.
2. Replace the room background with the referenced pink floral beauty-event backdrop.
Do not change the face. Do not change the action. Do not change the camera motion. Do not add speech, subtitles, text, logos, watermarks, split screen, or extra people.
Realistic phone video, stable identity, stable original motion, stable clothing, stable floral background."""


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("Missing GEMINI_API_KEY")
    for path in [SOURCE_VIDEO, CLOTHES, BACKGROUND]:
        if not path.exists():
            raise SystemExit(f"Missing input: {path}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = genai.Client(http_options={"api_version": "v1beta"}, api_key=api_key)

    uploaded_video = client.files.upload(file=str(SOURCE_VIDEO))
    print(f"Uploaded source video: {uploaded_video.uri}")
    source_video = types.Video(uri=uploaded_video.uri, mime_type="video/mp4")
    clothes = types.Image.from_file(location=str(CLOTHES))
    background = types.Image.from_file(location=str(BACKGROUND))

    config = types.GenerateVideosConfig(
        person_generation="allow_adult",
        aspect_ratio="9:16",
        number_of_videos=1,
        duration_seconds=8,
        resolution="720p",
        reference_images=[
            types.VideoGenerationReferenceImage(
                image=clothes,
                reference_type=types.VideoGenerationReferenceType.ASSET,
            ),
            types.VideoGenerationReferenceImage(
                image=background,
                reference_type=types.VideoGenerationReferenceType.ASSET,
            ),
        ],
    )

    operation = client.models.generate_videos(
        model=MODEL,
        prompt=PROMPT,
        video=source_video,
        config=config,
    )

    while not operation.done:
        print("Veo strict video-reference test is still generating...", flush=True)
        time.sleep(10)
        operation = client.operations.get(operation)

    result = operation.result
    if not result or not result.generated_videos:
        raise SystemExit("Veo returned no generated videos.")

    for index, generated_video in enumerate(result.generated_videos):
        if generated_video.video is None:
            continue
        print(f"Generated video URI: {generated_video.video.uri}")
        client.files.download(file=generated_video.video)
        out = OUT_DIR / f"veo31_video_reference_strict_{index:02d}.mp4"
        generated_video.video.save(str(out))
        print(f"Saved: {out}")


if __name__ == "__main__":
    main()
