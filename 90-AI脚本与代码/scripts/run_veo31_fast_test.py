#!/usr/bin/env python3
"""Run a Veo 3.1 Fast image-to-video test for the beauty try-on chain.

Requires:
  pip install google-genai pillow

Environment:
  GEMINI_API_KEY=...
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from google import genai
from google.genai import types


ROOT = Path("/Users/xlzj/Desktop/Seedance真人视频-美业活动")
DEFAULT_IMAGE = ROOT / "04-平台工作区/veo31_test_refs/start_frame.jpg"
DEFAULT_OUTPUT_DIR = ROOT / "02-生成产出/output_veo31_fast_test"

MODEL = "veo-3.1-fast-generate-preview"


PROMPT = """Create an 8-second vertical realistic beauty event video from the reference image.
Keep the same adult woman, same face identity, same hairstyle, same makeup, same earrings and necklace.
Keep the blue and white gingham ruffle outfit with white bow and layered white skirt.
Keep the pink floral beauty-event background and soft indoor commercial lighting.
The camera should feel like the original selfie-style beauty activity video.
The woman makes small natural skincare/beauty-promo motions: softly raises one hand near her cheek, blinks, slight head movement, calm confident expression.
Do not change the person's identity. Do not change the outfit style. Do not add text, logos, subtitles, watermarks, split screen, black borders, or extra people.
Realistic phone video, stable face, stable clothing, natural motion, polished beauty campaign look."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--aspect-ratio", default="9:16")
    parser.add_argument("--duration-seconds", type=int, default=8)
    parser.add_argument("--resolution", default="720p")
    parser.add_argument("--poll-seconds", type=int, default=10)
    parser.add_argument("--prompt", default=PROMPT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("Missing GEMINI_API_KEY. Export it first, then rerun this script.")
    if not args.image.exists():
        raise SystemExit(f"Reference image not found: {args.image}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    client = genai.Client(
        http_options={"api_version": "v1beta"},
        api_key=api_key,
    )

    image = types.Image.from_file(location=str(args.image))
    config = types.GenerateVideosConfig(
        person_generation="allow_adult",
        aspect_ratio=args.aspect_ratio,
        number_of_videos=1,
        duration_seconds=args.duration_seconds,
        resolution=args.resolution,
        negative_prompt=(
            "different person, changed face, changed outfit, text, logo, watermark, "
            "split screen, black borders, extra people, distorted hands, flickering clothes"
        ),
    )

    operation = client.models.generate_videos(
        model=MODEL,
        prompt=args.prompt,
        image=image,
        config=config,
    )

    while not operation.done:
        print("Veo video is still generating; checking again soon...", flush=True)
        time.sleep(args.poll_seconds)
        operation = client.operations.get(operation)

    result = operation.result
    if not result or not result.generated_videos:
        raise SystemExit("Veo finished but returned no generated videos.")

    for index, generated_video in enumerate(result.generated_videos):
        if generated_video.video is None:
            continue
        print(f"Generated video URI: {generated_video.video.uri}")
        client.files.download(file=generated_video.video)
        output_path = args.output_dir / f"veo31_fast_try_{index:02d}.mp4"
        generated_video.video.save(str(output_path))
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
