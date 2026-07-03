#!/usr/bin/env python3
"""Run Veo 3.1 Fast with original project assets only.

Inputs are:
- original frame extracted from the source video
- original 图三 clothing reference
- original 图二 background reference
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from google import genai
from google.genai import types


ROOT = Path("/Users/xlzj/Desktop/Seedance真人视频-美业活动")
PERSON = ROOT / "04-平台工作区/veo31_original_refs/original_person_frame.jpg"
CLOTHES = ROOT / "测试111换装测试/图三.jpg"
BACKGROUND = ROOT / "测试111换装测试/图二.jpg"
OUT_DIR = ROOT / "02-生成产出/output_veo31_fast_original_refs"

MODEL = os.environ.get("VEO_MODEL", "veo-3.1-generate-preview")

PROMPT = """Create an 8-second vertical realistic beauty event video using only the provided references.

Reference 1 is the original woman and selfie framing. Keep the same adult woman, same face identity, same hairstyle, same pearl earrings, same necklace, same skincare patches on the face, and similar close-up selfie camera framing.
Reference 2 is the target outfit. Replace the purple outfit with the blue and white gingham ruffle outfit: ruffled short sleeves, white bow at the chest, front buttons, blue-white checked fabric, and visible white layered skirt details where possible.
Reference 3 is the target background. Replace the room background with the pink floral beauty-event backdrop: pink display board, flowers, soft commercial beauty-event lighting.

The performance is silent and non-speaking: relaxed closed-mouth smile, soft blinking, tiny head movement, and one gentle hand movement near the cheek, similar to the original selfie video.
Keep the person's identity stable. Keep the motion subtle and calm. Keep clothing and floral background stable.
No text, logos, watermarks, subtitles, extra people, split screen, or black borders.
Realistic phone video, polished beauty campaign look."""


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("Missing GEMINI_API_KEY")
    for path in [PERSON, CLOTHES, BACKGROUND]:
        if not path.exists():
            raise SystemExit(f"Missing input: {path}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    client = genai.Client(http_options={"api_version": "v1beta"}, api_key=api_key)
    person = types.Image.from_file(location=str(PERSON))
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
                image=person,
                reference_type=types.VideoGenerationReferenceType.ASSET,
            ),
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
        config=config,
    )

    while not operation.done:
        print("Veo original-assets video is still generating...", flush=True)
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
        out = OUT_DIR / f"veo31_fast_original_refs_{index:02d}.mp4"
        generated_video.video.save(str(out))
        print(f"Saved: {out}")


if __name__ == "__main__":
    main()
