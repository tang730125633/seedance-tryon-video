#!/usr/bin/env python3
from pathlib import Path
import argparse
import json
import math
import subprocess
import sys


def video_duration(path: Path) -> float:
    try:
        import cv2
    except ImportError as exc:
        raise SystemExit("OpenCV/cv2 is required to infer video duration") from exc
    cap = cv2.VideoCapture(str(path))
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    cap.release()
    if not fps:
        raise RuntimeError(f"Cannot read fps: {path}")
    return frames / fps


def round_seconds(value: float, mode: str) -> int:
    if mode == "ceil":
        return int(math.ceil(value))
    if mode == "floor":
        return max(1, int(math.floor(value)))
    return max(1, int(round(value)))


def ensure_scan(root: Path):
    scan_script = Path(__file__).with_name("scan_tryon_clients.py")
    subprocess.run([sys.executable, str(scan_script), "--root", str(root)], check=True)
    return json.loads((root / "客户素材扫描结果.json").read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--rounding", choices=["ceil", "round", "floor"], default="ceil")
    parser.add_argument("--width", default="576")
    parser.add_argument("--height", default="1024")
    parser.add_argument("--target", default="Clothes")
    parser.add_argument("--max-seconds", type=int, default=0, help="Optional cap; 0 means no cap")
    args = parser.parse_args()

    root = Path(args.root)
    scan = ensure_scan(root)
    ready = [item for item in scan["clients"] if item["ready"]]
    missing = [item for item in scan["clients"] if not item["ready"]]
    if missing:
        for item in missing:
            print(f"{item['client']} 缺：{', '.join(item['missing'])}")
        raise SystemExit(f"素材未齐：{len(ready)}/{scan['total_count']} 个客户可生产")

    clients = []
    for item in ready:
        source = Path(item["person_video"])
        duration = video_duration(source)
        seconds = round_seconds(duration, args.rounding)
        if args.max_seconds:
            seconds = min(seconds, args.max_seconds)
        clients.append(
            {
                "id": item["client"],
                "name": item["client"],
                "source": item["person_video"],
                "clothes": item["clothes_reference"],
                "clothes_reference_type": item["clothes_reference_type"],
                "background": item["background_image"],
                "seconds": str(seconds),
                "source_duration_seconds": round(duration, 3),
                "width": str(args.width),
                "height": str(args.height),
                "target": str(args.target),
            }
        )

    manifest = {
        "source": str(root),
        "created_from": str(root / "客户素材扫描结果.json"),
        "seconds": "per-client-source-duration",
        "width": str(args.width),
        "height": str(args.height),
        "target": str(args.target),
        "duration_rounding": args.rounding,
        "clients": clients,
    }

    out = Path(args.out)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成长视频任务清单：{out}")
    for client in clients:
        print(f"{client['id']}: source={client['source_duration_seconds']}s -> seconds={client['seconds']}")


if __name__ == "__main__":
    main()

