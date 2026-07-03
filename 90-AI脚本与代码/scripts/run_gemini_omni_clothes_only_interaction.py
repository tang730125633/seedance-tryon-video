#!/usr/bin/env python3
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path("/Users/xlzj/Desktop/Seedance真人视频-美业活动")
OUT = ROOT / "02-生成产出/output_gemini_omni_interactions_clothes_only"
PERSON = ROOT / "04-平台工作区/veo31_original_refs/original_person_frame.jpg"
CLOTH = ROOT / "测试111换装测试/图三.jpg"
MODEL = "models/gemini-omni-flash-preview"


def image_part(path: Path) -> dict:
    return {
        "type": "image",
        "mime_type": "image/jpeg",
        "data": base64.b64encode(path.read_bytes()).decode("ascii"),
    }


def save_videos(result: dict) -> list[Path]:
    saved = []
    for step in result.get("steps", []):
        for item in step.get("content", []) or []:
            mime = item.get("mime_type") or item.get("mimeType")
            data = item.get("data")
            if mime == "video/mp4" and data:
                out = OUT / f"omni_clothes_only_{len(saved):02d}.mp4"
                out.write_bytes(base64.b64decode(data))
                saved.append(out)
    return saved


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Missing GEMINI_API_KEY", file=sys.stderr)
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    prompt = (
        "Create a silent vertical short video from the person reference image. "
        "Keep the same woman, same face, same hair, same makeup, same expression, same room background, "
        "same camera framing, and same gentle skincare hand motion. "
        "Only change her clothing to match the blue and white gingham ruffle outfit with the white bow from the clothing reference image. "
        "Do not change identity, do not change face, do not change background, do not add speech or lip movement."
    )
    payload = {
        "model": MODEL,
        "input": [
            {"type": "text", "text": prompt},
            image_part(PERSON),
            image_part(CLOTH),
        ],
    }
    request_path = OUT / "request_clothes_only.json"
    request_path.write_text(
        json.dumps(
            {
                "model": MODEL,
                "input": [
                    payload["input"][0],
                    {"type": "image", "mime_type": "image/jpeg", "source": str(PERSON)},
                    {"type": "image", "mime_type": "image/jpeg", "source": str(CLOTH)},
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    raw_path = OUT / "raw_clothes_only.json"
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        raw_path.write_bytes(raw)
        print(raw.decode("utf-8", errors="replace")[:1200])
        return 1

    raw_path.write_bytes(raw)
    result = json.loads(raw)
    if "error" in result:
        print(json.dumps(result["error"], ensure_ascii=False)[:1200])
        return 1
    saved = save_videos(result)
    print(json.dumps({"status": result.get("status"), "saved": [str(p) for p in saved]}, ensure_ascii=False))
    return 0 if saved else 1


if __name__ == "__main__":
    raise SystemExit(main())
